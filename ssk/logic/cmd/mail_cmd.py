#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


from flask import current_app

from .abstract_cmd import AbstractCmd
from ...globals.email_mgr import EmailMgr
from ...db import get_db


class MailTstCmd(AbstractCmd):
    def __init__(self):
        super().__init__("test")

    def action(self, a_param: list):
        my_ret_val = False

        if len(a_param) == 1:
            my_to = a_param[0]
            try:
                my_db_session = get_db().session
                my_email_mgr = EmailMgr(my_db_session)
                my_from = current_app.config["USER_EMAIL_SENDER_EMAIL"]
                my_email_mgr.send_test(my_from, my_to)
                my_db_session.commit()

                my_ret_val = True
                my_ret_mesg = '[[ print "OK: email sent" ]]'
            except Exception as ex:
                my_ret_mesg = '[[ print "Error: problems sending email {}" ]]'.format(ex)
        else:
            my_ret_mesg = self.help()

        return my_ret_val, my_ret_mesg

    def help(self, a_wrapped=True):
        return '[[ print "Usage: mail t <email>\nsends test email" ]]'


class MailCmd(AbstractCmd):
    def __init__(self):
        super().__init__("mail")
        self.reg_cmd(["t", "test"], MailTstCmd())

    def action(self, a_params: list):
        my_result = False
        my_mesg = self.help()

        my_cmd_name = self.get_params(a_params)
        my_cmd = self.get_cmd(my_cmd_name)
        if my_cmd is not None:
            my_result, my_mesg = my_cmd.exec(a_params)

        return my_result, my_mesg

    def help(self, a_wrapped=True):
        return '[[ print "Usage: mail {test}" ]]'

