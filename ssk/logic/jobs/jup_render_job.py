#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#

# from .base_job import BaseJob
# from ... import get_db
#
#
# class JupRenderJob(BaseJob):
#     def __init__(self, an_app, a_args):
#         super(JupRenderJob, self).__init__(an_app, a_args)
#
#     def work(self):
#         from ssk.models.db_stats import DBStats
#
#         with self._app.app_context():
#             try:
#                 my_all_tables = get_db().get_engine().table_names()
#                 my_log_tables = get_db().get_engine(bind_key="logdb").table_names()
#                 my_all_tables += my_log_tables
#
#                 for my_tmp_table in my_all_tables:
#                     my_count_sql = "select count(*) from {}".format(my_tmp_table)
#
#                     my_prefix = "func"
#                     if my_tmp_table not in my_log_tables:
#                         my_counter = get_db().engine.scalar(my_count_sql)
#                     else:
#                         my_prefix = "logdb"
#                         my_counter = get_db().get_engine(bind_key="logdb").scalar(my_count_sql)
#
#                     my_db_stat = DBStats()
#                     my_db_stat.type = "adhoc"
#                     my_db_stat.table = "{}.{}".format(my_prefix, my_tmp_table)
#                     my_db_stat.counter = my_counter
#
#                     my_db_session = get_db().session
#                     my_db_session.add(my_db_stat)
#                     my_db_session.commit()
#             except Exception as problem:
#                 self.write_to_log("Db Stat Failed {}".format(problem))
