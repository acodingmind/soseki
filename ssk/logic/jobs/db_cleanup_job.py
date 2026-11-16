#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#

from datetime import timedelta

from sqlalchemy import inspect, text

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
                    my_table_split = my_table_name.split('.')
                    if len(my_table_split) > 1:
                        my_bind_key, my_table_name = my_table_split[0], my_table_split[1]
                    else:
                        my_bind_key, my_table_name = None, my_table_split[0]

                    my_engine = get_db().engines[my_bind_key]

                    # the table name can't be a bound parameter, so only accept existing tables
                    if my_table_name not in inspect(my_engine).get_table_names():
                        raise ValueError("unknown table: {}".format(my_table_name))

                    my_pre = text("select count(*) from {} where created < :since".format(my_table_name))
                    my_sql = text("delete from {} where created < :since".format(my_table_name))
                    with my_engine.begin() as my_conn:
                        my_to_delete = my_conn.scalar(my_pre, {"since": my_since})
                        my_conn.execute(my_sql, {"since": my_since})
                        my_check = my_conn.scalar(my_pre, {"since": my_since})

                    if my_check == 0:
                        self.write_to_audit("OK", "cleanup table {} until {} ({} records deleted)".format(my_table_name, my_since.strftime("%D %H:%M:%S"), my_to_delete))
                    self.write_to_log("Db Cleanup Finished successfully")
                except Exception as problem:
                    self.write_to_log("Db Cleanup {} {} Failed {}".format(my_table_name, my_since, problem))
                    self.write_to_audit("NOK", "cleanup table {} failed: {}".format(my_table_name, str(problem)[:80]))
            else:
                self.write_to_log("Db Cleanup Failed not enough arguments")
