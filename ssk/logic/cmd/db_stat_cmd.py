#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


from flask import current_app

from ssk.logic.cmd.abstract_cmd import AbstractCmd
from ssk.logic.jobs.db_stat_job import DbStatJob


class DbStatCmd(AbstractCmd):
    def __init__(self):
        super().__init__("dbstat")

    def action(self, a_params: list):
        from ssk.globals.cmd_processor import CmdProcessor

        my_retval = None

        if len(a_params) == 0:
            my_task = DbStatJob(current_app, a_args=["dbstat"])

            CmdProcessor.submit_cmd(my_task)
            my_mesg = '[[ print "OK: started job dbstat {}" ]]'.format(my_task.get_task_id())
            my_retval = my_task.get_task_id()
        else:
            my_mesg = '[[ print "Error: action name is missing" ]]'

        return my_retval, my_mesg

    def help(self, a_wrapped=True):
        return '[[ print "Usage: dbstat\nstarts a dbstat job" ]]'