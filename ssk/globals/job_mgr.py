#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


import os

from flask import current_app
from sqlalchemy.orm import exc
from sqlalchemy import and_, desc

from ..logic.jobs.base_job import BaseJob
from ..logic.jobs.empty_job import EmptyJob
from ..models.job import Job
from ..db import get_db


class JobMgr:
    _queued_jobs = None
    _active_jobs = None

    def __init__(self):
        # every thread has new g object, meaning also new JobMgr
        # in case of a progress request from the gui, new thread needs to load jobs from the db
        # to be able to monitor status
        self._active_jobs = {}

        my_all_jobs = get_db().session.query(Job).filter(Job.status == BaseJob.IN_PROG_STATUS).order_by(desc(Job.created)).all()

        for my_tmp_job in my_all_jobs:
            my_tmp_task = EmptyJob(current_app, a_args=my_tmp_job.action)
            my_tmp_task.set_executor_id(my_tmp_job.user_id)
            my_tmp_task.set_task_id(my_tmp_job.task_id)
            my_tmp_task.set_progress(my_tmp_job.progress)
            my_tmp_task.set_logfile(my_tmp_job.logfile)

            my_tmp_task.set_job_tracker(self)
            self._active_jobs[my_tmp_task.get_task_id()] = my_tmp_task

        self._queued_jobs = {}

        my_all_jobs = get_db().session.query(Job).filter(Job.status == BaseJob.QUEUED).order_by(desc(Job.created)).all()

        for my_tmp_job in my_all_jobs:
            my_tmp_task = EmptyJob(current_app, a_args=my_tmp_job.action)
            my_tmp_task.set_executor_id(my_tmp_job.user_id)
            my_tmp_task.set_task_id(my_tmp_job.task_id)
            my_tmp_task.set_progress(my_tmp_job.progress)
            my_tmp_task.set_logfile(my_tmp_job.logfile)

            my_tmp_task.set_job_tracker(self)
            self._queued_jobs[my_tmp_task.get_task_id()] = my_tmp_task

    def total_active(self):
        return len(self._active_jobs)

    def total_queued(self):
        return len(self._queued_jobs)

    def is_active(self, a_job_id):
        return a_job_id in self._active_jobs.keys()

    def is_queued(self, a_job_id):
        return a_job_id in self._queued_jobs.keys()

    def queue_job(self, a_job):
        a_job.set_job_tracker(self)
        self._queued_jobs[a_job.get_task_id()] = a_job
        a_job.queue()

        return a_job

    def start_job(self, a_job):
        if a_job.get_task_id() in self._queued_jobs.keys():
            self._queued_jobs.pop(a_job.get_task_id())

        self._active_jobs[a_job.get_task_id()] = a_job
        a_job.start()

        return a_job

    def get_last_active_job_by_user(self, a_user_id, a_name=None):
        if a_name is not None:
            return get_db().session.query(Job).filter(and_(Job.user_id == a_user_id,
                                                           Job.status == BaseJob.IN_PROG_STATUS,
                                                           Job.name == a_name)).order_by(desc(Job.created)).first()
        else:
            return get_db().session.query(Job).filter(and_(Job.user_id == a_user_id,
                                                           Job.status == BaseJob.IN_PROG_STATUS)).order_by(desc(Job.created)).first()

    def get_all_active_jobs_by_user(self, a_user_id):
        my_all_jobs = get_db().session.query(Job).filter(and_(Job.user_id == a_user_id, Job.status == BaseJob.IN_PROG_STATUS)).order_by(desc(Job.created)).all()

        return my_all_jobs

    def get_all_jobs_by_user(self, a_user_id):
        my_all_jobs = get_db().session.query(Job).filter(and_(Job.user_id == a_user_id)).order_by(desc(Job.created)).all()

        return my_all_jobs

    def get_progress(self, a_job_id):
        my_ret_val = 0

        if a_job_id != "-":
            my_ret_val = 100

            if self.is_active(a_job_id):
                my_job = self._active_jobs[a_job_id]
                my_ret_val = my_job.get_progress()

        return my_ret_val

    def get_logfile(self, a_job_id):
        my_retval = None
        my_job = Job.get_by_key(a_job_id)

        if my_job is not None and os.path.exists(my_job.logfile):
            my_retval = my_job.logfile

        return my_retval

    def stop_job(self, a_job_id):
        my_ret_val = False
        my_mesg = ""

        if self.is_active(a_job_id):
            my_job = self._active_jobs[a_job_id]
            my_job.stop()

            self._active_jobs.pop(a_job_id)

            my_ret_val = True
        elif self.is_queued(a_job_id):
            my_job = self._queued_jobs[a_job_id]
            my_job.stop()

            self._queued_jobs.pop(a_job_id)

            my_ret_val = True
        else:
            my_mesg = "Error: Job {} Not Found".format(a_job_id)

        return my_ret_val, my_mesg

    def finish_job(self, a_job_id):
        my_ret_val = False
        if self.is_active(a_job_id):
            self._active_jobs.pop(a_job_id)

            my_ret_val = True

        return my_ret_val

    def stop_all(self, a_status):
        my_to_stop = {}
        if a_status == BaseJob.IN_PROG_STATUS:
            my_to_stop = dict(self._active_jobs)
        if a_status == BaseJob.QUEUED:
            my_to_stop = dict(self._queued_jobs)

        my_cnt = 0
        for my_job_id in my_to_stop:
            my_res, _ = self.stop_job(my_job_id)
            if my_res:
                my_cnt += 1

        return True, "Stopped {} jobs".format(my_cnt)

    def del_all(self, a_status):
        my_cnt = 0
        my_all = Job.query.filter_by(status=a_status).all()
        for my_tmp_job in my_all:
            my_res, _ = self.delete_job(my_tmp_job.task_id)
            if my_res:
                my_cnt += 1

        return True, "Deleted {} jobs".format(my_cnt)

    def delete_job(self, a_job_id):
        my_retval = False

        from ..models.job import Job
        from ..db import get_db

        try:
            if not self.is_active(a_job_id) and not self.is_queued(a_job_id):
                my_job = Job.get_by_key(a_job_id)
                if my_job is not None:
                    if my_job.logfile is not None and os.path.exists(my_job.logfile):
                        try:
                            os.remove(my_job.logfile)
                        except Exception as e:
                            current_app.logger.error("Task {} cannot remove logfile {} {}".format(a_job_id,
                                                                                                  my_job.logfile,
                                                                                                  e))
                    else:
                        current_app.logger.error("Task {} logfile {} does not exist".format(a_job_id, my_job.logfile))

                    Job.query.filter_by(task_id=a_job_id).delete()
                    get_db().session.commit()

                my_retval = True
                my_mesg = "OK: Job {} deleted".format(a_job_id)
            else:
                my_mesg = "Error: Cannot delete active or queued job {} ".format(a_job_id)

        except exc.NoResultFound:
            my_mesg = "Error: Job {} not found".format(a_job_id)

        return my_retval, my_mesg
