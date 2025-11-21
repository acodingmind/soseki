#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


from flask import current_app
from sqlalchemy import desc

from .abstract_cmd import AbstractCmd
from ..jobs.base_job import BaseJob
from ...models.job import Job
from ...utils import get_padding, get_ago
from ...logic.jobs.empty_job import EmptyJob


class JobPrintCmd(AbstractCmd):
    def __init__(self):
        super().__init__("list")

    def action(self, a_param: list):
        my_mesg = '[[ print "\n'

        my_template = "{} {} {} {} {}\n"
        my_tasks = Job.query.order_by(desc(Job.created))
        my_mesg = my_mesg + my_template.format(get_padding("id", 6),
                                               get_padding("task id", 38),
                                               get_padding("name", 50),
                                               get_padding("status", 12),
                                               get_padding("%", 6))

        my_mesg = my_mesg + my_template.format("_" * 6,
                                               "_" * 38,
                                               "_" * 50,
                                               "_" * 12,
                                               "_" * 6)

        for my_tmp_task in my_tasks:
            my_mesg = my_mesg + my_template.format(get_padding(my_tmp_task.id, 6),
                                                   get_padding(my_tmp_task.task_id, 38),
                                                   get_padding(my_tmp_task.name, 50),
                                                   get_padding(my_tmp_task.status, 12),
                                                   get_padding(my_tmp_task.progress, 6))

            my_time = " "
            if my_tmp_task.done is not None:
                my_time = get_ago((my_tmp_task.done - my_tmp_task.started).seconds, a_suffix="")

            my_start_finish = "s: " + str(my_tmp_task.started)[:19] + " " + "f: " + str(my_tmp_task.done)[:19]

            my_mesg = my_mesg + "{} {} {}\n\n".format(" " * 6,
                                                      get_padding(my_time, 38),
                                                      get_padding(my_start_finish, 50)
                                                      )

        my_mesg = my_mesg + '" ]]'

        return True, my_mesg

    def help(self, a_wrapped=True):
        return '[[ print "Usage: job ls\nprints the list of all jobs in the system" ]]'


class JobRunCmd(AbstractCmd):
    def __init__(self):
        super().__init__("run")

    def action(self, a_params: list):
        from ssk.globals.cmd_processor import CmdProcessor

        my_retval = None

        if len(a_params) == 1:
            my_args = a_params[0]
            my_task = EmptyJob(current_app, a_args=my_args)

            CmdProcessor.submit_cmd(my_task)
            my_mesg = '[[ print "OK: started job {} {}" ]]'.format(my_args, my_task.get_task_id())
            my_retval = my_task.get_task_id()
        else:
            my_mesg = '[[ print "Error: action name is missing" ]]'

        return my_retval, my_mesg

    def help(self, a_wrapped=True):
        return '[[ print "Usage: job start <action name>\nstarts a job" ]]'


class JobKillCmd(AbstractCmd):
    def __init__(self):
        super().__init__("kill")

    def action(self, a_params: list):
        from ssk.lg import get_logic

        my_retval = False

        if len(a_params) == 1:
            my_task_id = a_params.pop(0)

            if my_task_id == "all_a":
                my_retval, my_mesg = get_logic().get_job_mgr().stop_all(a_status=BaseJob.IN_PROG_STATUS)
            elif my_task_id == "all_q":
                my_retval, my_mesg = get_logic().get_job_mgr().stop_all(a_status=BaseJob.QUEUED)
            else:
                my_retval, my_mesg = get_logic().get_job_mgr().stop_job(my_task_id)
        else:
            my_mesg = '[[ print "Error: job id is missing" ]]'

        return my_retval, my_mesg

    def help(self, a_wrapped=True):
        return '[[ print "Usage: job kill <action name>\nstops a job" ]]'


class JobDelCmd(AbstractCmd):
    def __init__(self):
        super().__init__("delete")

    def action(self, a_params: list):
        from ssk.lg import get_logic

        my_retval = False

        if len(a_params) == 1:
            my_task_id = a_params.pop(0)

            if my_task_id == "all_s":
                my_retval, my_mesg = get_logic().get_job_mgr().del_all(a_status=BaseJob.STOPPED_STATUS)
            elif my_task_id == "all_d":
                my_retval, my_mesg = get_logic().get_job_mgr().del_all(a_status=BaseJob.DONE_STATUS)
            else:
                my_retval, my_mesg = get_logic().get_job_mgr().delete_job(my_task_id)
        else:
            my_mesg = '[[ print "Error: job id is missing" ]]'

        return my_retval, my_mesg

    def help(self, a_wrapped=True):
        return '[[ print "Usage: job del <jobid>\ndeletes a job" ]]'


class JobCmd(AbstractCmd):
    def __init__(self):
        super().__init__("jobs")
        self.reg_cmd(["l", "list"], JobPrintCmd())
        self.reg_cmd(["r", "run"], JobRunCmd())
        self.reg_cmd(["k", "kill"], JobKillCmd())
        self.reg_cmd(["d", "del"], JobDelCmd())

    def action(self, a_params: list):
        my_result = False
        my_mesg = self.help()

        my_cmd_name = self.get_params(a_params)
        my_cmd = self.get_cmd(my_cmd_name)
        if my_cmd is not None:
            my_result, my_mesg = my_cmd.exec(a_params)

        return my_result, my_mesg

    def help(self, a_wrapped=True):
        return '[[ print "Usage: job {list | run | kill | delete}" ]]'
