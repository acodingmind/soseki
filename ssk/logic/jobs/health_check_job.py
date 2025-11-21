#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#

import os
from datetime import datetime

import psutil
import requests
from _datetime import timedelta
from flask import current_app

from .base_job import BaseJob
from ... import get_db
from ...globals.api_gate import ApiGate


class HealthCheckJob(BaseJob):
    def __init__(self, an_app, a_args):
        super(HealthCheckJob, self).__init__(an_app, a_args)

    def work(self):
        with self._app.app_context():
            try:
                from ...models.status import Status
                from ...models.user import User
                from ...models.audit import Audit
                from ...models.setting import Setting

                my_status = Status()

                my_process = psutil.Process(os.getpid())

                my_api_status = "open"
                if not ApiGate.is_open():
                    my_api_status = "closed"

                my_status.api_status = my_api_status
                my_status.api_now_threshold = current_app.config["API_ACTIVE_NOW"]
                my_status.api_active_now = ApiGate.num_active_keys()
                my_status.api_max_active = current_app.config["MAX_ACTIVE_KEYS"]
                my_status.api_total = ApiGate.num_total_keys()

                my_all_users = User.query.all()
                last_15min = datetime.now() - timedelta(minutes=15)
                my_loggedin_users = User.query.filter(User.last_access > last_15min).all()

                my_status.users = len(my_all_users)
                my_status.users_active = len(my_loggedin_users)

                my_all_settings = Setting.query.all()
                my_status.conf_keys = len(my_all_settings)

                my_all_audit = Audit.query.all()
                my_status.audit_cnt = len(my_all_audit)

                my_url = current_app.config["ROOT_URL"]

                my_resp_time = -1
                if my_url != "":
                    my_now = datetime.now()
                    my_response = requests.get(my_url)
                    if my_response.status_code == 200:
                        my_resp_time = (datetime.now() - my_now).total_seconds()
                else:
                    my_resp_time = 0

                my_status.response_time = my_resp_time
                my_status.mem = round(my_process.memory_info().rss / (1024 ** 2), 2)

                get_db().session.add(my_status)
                get_db().session.commit()
            except Exception as problem:
                self.write_to_log("Health Check Failed {}".format(problem))
