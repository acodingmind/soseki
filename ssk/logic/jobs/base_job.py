#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#

import tempfile
import os
import uuid
import json
from datetime import datetime
from abc import ABC, abstractmethod
from flask_login import current_user
from os.path import exists


class BaseJob(ABC):
    QUEUED = "QUEUED"
    IN_PROG_STATUS = "IN PROGRESS"
    STOPPED_STATUS = "STOPPED"
    DONE_STATUS = "DONE"

    _app = None
    _thread = None
    _task_id = None
    _args = None
    _progress = None
    _job_tracker = None
    _executor_id = None
    _logfile = None
    _status = None

    def __init__(self, an_app, an_args):
        self._app = an_app._get_current_object()

        if current_user._get_current_object() is not None and not current_user.is_anonymous:
            self._executor_id = current_user.id

        self._task_id = str(uuid.uuid4())
        self._args = an_args

    def set_executor_id(self, an_executor_id):
        self._executor_id = an_executor_id

    def get_current_app(self):
        return self._app

    def set_job_tracker(self, a_job_tracker):
        self._job_tracker = a_job_tracker

    def set_task_id(self, a_task_id):
        self._task_id = a_task_id

    def get_task_id(self):
        return self._task_id

    def get_args(self):
        return self._args

    def write_to_log(self, a_message):
        if self._logfile is not None and exists(self._logfile.name):
            my_now = datetime.now()
            my_message = "{} {}: {}\n".format(self._task_id,
                                              my_now.strftime("%Y-%m-%d %H:%M:%S"),
                                              a_message)
            self._logfile.write(my_message)
            self._logfile.flush()
        else:
            if self._logfile is None:
                self._app.logger.error("Task {} cannot log {}. Logfile name is not set".format(self._task_id,
                                                                                               a_message))
            else:
                if not exists(self._logfile.name):
                    self._app.logger.error("Task {} cannot log {}. Logfile does not exist".format(self._task_id,
                                                                                              a_message))

    def write_to_audit(self, a_status, a_message):
        with self._app.app_context():
            from ssk import Audit, get_db

            my_audit = Audit()
            my_audit.by_user = "SYSTEM"
            my_audit.category = "JOBS"
            my_audit.description = "{} job: {}".format(a_message, self.get_args())
            my_audit.status = a_status
            get_db().session.add(my_audit)
            get_db().session.commit()

    def get_args_str(self):
        try:
            my_ret_val = json.dumps(self._args)
        except Exception:
            my_ret_val = "Not Serializable args"

        return my_ret_val.replace("\"", "")

    def get_progress(self):
        return self._progress

    def get_logfile(self):
        if self._logfile is not None:
            return self._logfile.name

        return None

    def set_logfile(self, a_file):
        if a_file is not None and os.path.exists(a_file):
            self._logfile = open(a_file, 'a')

    def log_queue(self):
        self._status = BaseJob.QUEUED

        from ...models.job import Job

        with self._app.app_context():
            my_trigger = Job()
            my_trigger.task_id = self._task_id
            my_trigger.user_id = self._executor_id
            my_trigger.status = BaseJob.QUEUED
            my_trigger.progress = 0

            try:
                my_log_dir = self._app.config["LOG_DIR"]
                self._logfile = tempfile.NamedTemporaryFile(dir=my_log_dir, delete=False, mode="w")
                self.write_to_log("queued")

                my_trigger.logfile = self._logfile.name
            except FileNotFoundError:
                self._app.logger.error("Task {} cannot create logfile".format(self._task_id))

            if len(self._args) > 0:
                my_trigger.name = self._args[0]
            else:
                my_trigger.name = "noname"
            my_trigger.action = self.get_args_str()
            my_trigger.started = datetime.now()

            from ...db import get_db
            get_db().session.add(my_trigger)
            get_db().session.commit()

    def log_start(self):
        self.set_status(BaseJob.IN_PROG_STATUS)
        self.write_to_log("started")

    def log_done(self, an_app):
        with an_app.app_context():
            self.set_status(BaseJob.DONE_STATUS)

        self.write_to_log("done")

    def queue(self):
        self.log_queue()

    def start(self):
        self.log_start()
        self.execute(self._app)

    def stop(self):
        self.set_status(BaseJob.STOPPED_STATUS)

        if self._logfile is not None and exists(self._logfile.name):
            self.write_to_log("stopped")
            self._logfile.close()

    def done(self):
        self.set_status(BaseJob.DONE_STATUS)

        if self._logfile is not None and exists(self._logfile.name):
            self.write_to_log("done")
            self._logfile.close()

    def set_progress(self, a_val):
        self._progress = a_val

        with self._app.app_context():
            from ...models.job import Job
            from ...db import get_db
            my_trigger = get_db().session.query(Job).filter_by(task_id=self._task_id).first()

            if my_trigger is not None:
                my_trigger.progress = self._progress

                get_db().session.add(my_trigger)
                get_db().session.commit()

                if my_trigger.status == BaseJob.STOPPED_STATUS or my_trigger.status == BaseJob.DONE_STATUS:
                    self._app.logger.info("Task {} is {}".format(self._task_id, BaseJob.STOPPED_STATUS))
                    raise SystemExit()
            else:
                self._app.logger.info("Task {} not found".format(self._task_id))
                raise SystemExit()

    def execute(self, an_app):
        self.write_to_log("start execution")
        self.set_progress(0)
        try:
            self.work()
        except Exception as e:
            self.write_to_log("job execute error {}".format(e))
        finally:
            self.write_to_log("finally")

        self.log_done(an_app)
        self.set_progress(100)
        self._job_tracker.finish_job(self._task_id)

    def get_status(self):
        return self._status

    def set_status(self, a_status):
        self._status = a_status

        from ...models.job import Job
        from ...db import get_db

        with self._app.app_context():
            my_trigger = Job.get_by_key(self._task_id)

            if my_trigger is not None:
                my_trigger.status = a_status
                my_trigger.done = datetime.now()

                get_db().session.add(my_trigger)
                get_db().session.commit()
            else:
                self._app.logger.error("Task {} not found".format(self._task_id))
                raise SystemExit()

    @abstractmethod
    def work(self):
        ...
