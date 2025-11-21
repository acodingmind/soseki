#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#

from flask import current_app

from ssk.logic.cmd.abstract_cmd import AbstractCmd
from ssk.logic.jobs.db_cleanup_job import DbCleanupJob


class DbCleanupCmd(AbstractCmd):
    def __init__(self):
        super().__init__("dbcleanup")

    def action(self, a_params: list):
        from ssk.globals.cmd_processor import CmdProcessor

        my_retval = None

        if len(a_params) == 0:
            if "DB_CLEANUP" in current_app.config.keys():
                my_to_clean = current_app.config["DB_CLEANUP"]
                my_mesg = '[[ print "OK: cleaning up '

                for my_tmp_table in my_to_clean.keys():
                    my_task = DbCleanupJob(current_app, a_args=["dbcleanup {}".format(my_tmp_table), my_tmp_table, my_to_clean[my_tmp_table]])
                    CmdProcessor.submit_cmd(my_task)
                    my_mesg += "{}, ".format(my_tmp_table)
                    my_retval = my_task.get_task_id()

                my_mesg += '" ]]'
            else:
                my_mesg = '[[ print "Error: DB_CLEANUP not set" ]]'
        else:
            my_mesg = '[[ print "Error: action name is missing" ]]'

        return my_retval, my_mesg

    def help(self, a_wrapped=True):
        return '[[ print "Usage: dbcleanup\nstarts a dbcleanup job" ]]'