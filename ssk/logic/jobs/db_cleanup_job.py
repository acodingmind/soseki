#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#

from datetime import timedelta

from .base_job import BaseJob
from ... import get_db
from ...utils import now


class DbCleanupJob(BaseJob):
    def __init__(self, an_app, a_args):
        super(DbCleanupJob, self).__init__(an_app, a_args)

    def work(self):
        with self._app.app_context():
            my_args = self.get_args()

            if len(my_args) == 3:
                my_table_name = my_args[1]
                my_days = my_args[2]

                my_since = now() - timedelta(days=my_days)
                self.write_to_log("cleanup {} start {} until {}".format(my_args[0], my_table_name, my_since))

                try:
                    my_engine = None
                    my_table_split = my_table_name.split('.')
                    if len(my_table_split) > 1:
                        my_table_name = my_table_split[1]
                        my_engine = get_db().get_engine(bind_key=my_table_split[0])
                    else:
                        my_table_name = my_table_split[0]
                        my_engine = get_db().engine

                    my_pre = "select count(*) from {} where created < '{}'".format(my_table_name, my_since)
                    my_to_delete = my_engine.scalar(my_pre)
                    my_sql = "delete from {} where created < '{}'".format(my_table_name, my_since)
                    my_engine.execute(my_sql)
                    my_check = my_engine.scalar(my_pre)
                    if my_check == 0:
                        self.write_to_audit("OK", "cleanup table {} until {} ({} records deleted)".format(my_table_name, my_since.strftime("%D %H:%M:%S"), my_to_delete))
                except Exception as problem:
                    self.write_to_log("Db Cleanup {} {} Failed {}".format(my_table_name, my_since, problem))

                self.write_to_log("Db Cleanup Finished successfully")
            else:
                self.write_to_log("Db Cleanup Failed not enough arguments")
