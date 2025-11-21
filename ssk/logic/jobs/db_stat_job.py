#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#

from .base_job import BaseJob
from sqlalchemy import text
from ... import get_db


class DbStatJob(BaseJob):
    def __init__(self, an_app, a_args):
        super(DbStatJob, self).__init__(an_app, a_args)

    def work(self):
        from ssk.models.db_stats import DBStats

        with self._app.app_context():
            try:
                my_all_tables_dict = get_db().metadata.tables.keys()
                my_all_tables = [my_tmp_name for my_tmp_name in my_all_tables_dict]
                my_log_tables_dict = get_db().metadatas['logdb'].tables.keys()
                my_log_tables = [my_tmp_name for my_tmp_name in my_log_tables_dict]
                my_all_tables += my_log_tables

                for my_tmp_table in my_all_tables:
                    my_count_sql = text("select count(*) from {}".format(my_tmp_table))

                    my_prefix = "func"
                    if my_tmp_table not in my_log_tables:
                        my_counter = get_db().session.scalar(my_count_sql)
                    else:
                        my_count_sql = text("select count(*) from {}".format(my_tmp_table))
                        my_prefix = "logdb"

                        my_log_engine = get_db().engines['logdb']
                        my_counter = get_db().session.execute(my_count_sql, None, bind_arguments={'bind': my_log_engine}).scalar()

                    my_db_stat = DBStats()
                    my_db_stat.type = "adhoc"
                    my_db_stat.table = "{}.{}".format(my_prefix, my_tmp_table)
                    my_db_stat.counter = my_counter

                    my_db_session = get_db().session
                    my_db_session.add(my_db_stat)
                    my_db_session.commit()
            except Exception as problem:
                self.write_to_log("Db Stat Failed {}".format(problem))
