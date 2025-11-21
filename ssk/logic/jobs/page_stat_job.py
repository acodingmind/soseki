#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#

from datetime import timedelta

from flask import current_app
from sqlalchemy import and_

from .base_job import BaseJob
from ... import get_db
from ...models.access import Access
from statistics import mean

from ...utils import now


class PageStatJob(BaseJob):
    def __init__(self, an_app, a_args):
        super(PageStatJob, self).__init__(an_app, a_args)

    def work(self):
        from ssk.models.stats import Stats

        with self._app.app_context():
            try:
                my_admin_user = current_app.config["ADMIN_NAME"]
                my_processed_id = Stats.get_last_processed_id()

                my_since = now() - timedelta(days=7)

                my_per_page = get_db().session.query(Access).filter(and_(Access.id > my_processed_id,
                                                                         Access.created > my_since,
                                                                         Access.user != my_admin_user)).all()

                my_tmp_mean = {}

                my_db_session = get_db().session
                for my_tmp_access in my_per_page:
                    my_date = "{}-{}-{}".format(my_tmp_access.created.year, my_tmp_access.created.month, my_tmp_access.created.day)

                    if my_tmp_access.response != "200 OK":
                        my_page = "NOTOK"
                    else:
                        my_split = my_tmp_access.path.split("/")
                        if len(my_split) > 0:
                            my_page = my_split[1]

                    if not my_page.startswith("?"):
                        if my_date not in my_tmp_mean.keys():
                            my_tmp_mean[my_date] = {}

                        if my_page not in my_tmp_mean[my_date].keys():
                            my_tmp_mean[my_date][my_page] = []

                        my_stats_db = get_db().session.query(Stats).filter(and_(Stats.day == my_date, Stats.path == my_page)).first()
                        if my_stats_db is None:
                            my_stats_db = Stats()
                            my_stats_db.day = my_date
                            my_stats_db.path = my_page
                            my_stats_db.hits = 0
                            my_stats_db.last_processed = 0
                            my_stats_db.mean_response_time = 0
                            my_stats_db.max_response_time = 0

                        if my_stats_db.last_processed < my_tmp_access.id:
                            my_tmp_mean[my_date][my_page].append(my_tmp_access.response_time)

                            my_stats_db.last_processed = my_tmp_access.id
                            if my_tmp_access.response_time > my_stats_db.max_response_time:
                                my_stats_db.max_response_time = my_tmp_access.response_time

                            my_stats_db.mean_response_time = mean(my_tmp_mean[my_date][my_page])
                            my_stats_db.hits += 1

                        my_db_session.add(my_stats_db)

                my_db_session.commit()

            except Exception as problem:
                self.write_to_log("Page Stat Failed {}".format(problem))
