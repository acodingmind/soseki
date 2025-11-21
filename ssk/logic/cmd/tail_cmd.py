#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


import os

from flask import current_app
from sqlalchemy import asc

from ...models.audit import Audit
from ...utils import get_padding, get_timestamp_str
from .abstract_cmd import AbstractCmd


class TailAuditCmd(AbstractCmd):
    def __init__(self):
        super().__init__("audit")

    def action(self, a_param: list):
        my_mesg = '[[ print "\n'
        my_audit_list = []

        if len(a_param) > 0:
            if a_param[0] == "nok":
                my_audit_list = Audit.query.filter(Audit.status != "OK").order_by(asc(Audit.created)).limit(1000)
        else:
            my_audit_list = Audit.query.order_by(asc(Audit.created)).limit(1000)

        my_template = "{} {} {} {} {}\n"
        my_mesg = my_mesg + my_template.format(get_padding("id", 6),
                                               get_padding("by", 25),
                                               get_padding("category", 10),
                                               get_padding("status", 10),
                                               get_padding("created", 20))

        my_mesg = my_mesg + my_template.format("_" * 6,
                                               "_" * 25,
                                               "_" * 10,
                                               "_" * 10,
                                               "_" * 20)

        for my_tmp_audit in my_audit_list:
            my_description = my_tmp_audit.description
            my_description = my_description.replace("`", "")

            my_mesg = my_mesg + my_template.format(get_padding(my_tmp_audit.id, 6),
                                                   get_padding(my_tmp_audit.by_user, 25),
                                                   get_padding(my_tmp_audit.category, 10),
                                                   get_padding(my_tmp_audit.status, 10),
                                                   get_padding(my_tmp_audit.created, 20))

            my_mesg = my_mesg + "{} {}\n".format(" " * 6, get_padding(my_description, 250))

        my_mesg = my_mesg + '" ]]'

        return True, my_mesg

    def help(self, a_wrapped=True):
        return '[[ print "Usage: tail audit {nok}\nprints the list of 1000 recent audit entries" ]]'


class TailLogCmd(AbstractCmd):
    def __init__(self):
        super().__init__("log")

    def action(self, a_params: list):
        my_result = False
        my_mesg = self.help()

        my_lines = 100
        if len(a_params) == 1:
            try:
                my_lines = int(a_params.pop(0))
                if my_lines > 10000:
                    my_lines = 0
                    my_mesg = "Error: parameter must be an integer (0-10000)"

            except Exception:
                my_lines = 0
                my_mesg = "Error: parameter must be an integer (0-10000)"

        if my_lines > 0:
            my_mesg = '[[ print "\n'
            my_bufsize = 8192
            my_fname = current_app.config["LOG_FILE"]
            my_fsize = os.stat(my_fname).st_size

            my_iter = 0
            with open(my_fname) as f:
                if my_bufsize > my_fsize:
                    my_bufsize = my_fsize - 1

                data = []

                while True:
                    my_iter += 1
                    my_loc = my_fsize - my_bufsize * my_iter
                    if my_loc < 0:
                        my_loc = my_fsize - my_bufsize

                        f.seek(my_loc)
                        data.extend(f.readlines())
                        if len(data) >= my_lines or f.tell() == 0:
                            my_line = "{}\n".format(''.join(data[-my_lines:]))
                            my_line = my_line.replace("[", "")
                            my_line = my_line.replace("]", "")
                            my_line = my_line.replace("'", "")
                            my_line = my_line.replace("\"", "")
                            my_line = my_line.replace("\u001b", "")

                            my_mesg = my_mesg + my_line
                            break

            my_result = True
            my_mesg = my_mesg + '" ]]'
            my_mesg = '[[ ts "{}" ]]'.format(get_timestamp_str()) + my_mesg

        return my_result, my_mesg

    def help(self, a_wrapped=True):
        return '[[ print "Usage: tail error [num_of_lines]" ]]'


class TailCmd(AbstractCmd):
    def __init__(self):
        super().__init__("tail")
        self.reg_cmd(["l", "log"], TailLogCmd())
        self.reg_cmd(["a", "audit"], TailAuditCmd())

    def action(self, a_params: list):
        my_result = False
        my_mesg = self.help()

        my_cmd_name = self.get_params(a_params)
        my_cmd = self.get_cmd(my_cmd_name)
        if my_cmd is not None:
            my_result, my_mesg = my_cmd.exec(a_params)

        return my_result, my_mesg

    def help(self, a_wrapped=True):
        return '[[ print "Usage: tail {log | audit}" ]]'
