#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


from flask_login import current_user

from ...db import get_db
from ...models.audit import Audit


class AbstractCmd:
    ANON = 1
    USER = 2
    MEMBER = 3
    ROOT = 4

    HELP_STR = '[[ print "? for help" ]]'
    PRINT_CMD = '[[ print "\n'

    _supported_cmd = None
    _name = None
    _ctx = None
    _type = None

    def __init__(self, a_name, a_type=ROOT):
        self._supported_cmd = {}
        self._name = a_name
        self._ctx = a_name
        self._type = a_type

    def get_name(self):
        return self._name

    def reg_cmd(self, a_cmd_names: list, a_cmd):
        for my_tmp_cmd_name in a_cmd_names:
            self._supported_cmd[my_tmp_cmd_name] = a_cmd

    def get_all_cmds(self):
        return self._supported_cmd

    def get_params(self, a_params):
        if len(a_params) > 0:
            return a_params.pop(0)

        return "?"

    def get_cmd(self, a_cmd):
        my_retval = None

        if a_cmd in self._supported_cmd:
            my_retval = self._supported_cmd[a_cmd]

        return my_retval

    def sos(self, a_params: list):
        if len(a_params) == 1 and (a_params[0] == "help" or a_params[0] == "?"):
            return True

        return False

    def has_access(self):
        my_user_class = AbstractCmd.ANON

        if not current_user.is_anonymous:
            my_user_class = AbstractCmd.USER

            if current_user.is_admin():
                my_user_class = AbstractCmd.ROOT

        return self._type <= my_user_class

    def exec(self, a_params: list):
        if self.sos(a_params):
            return True, self.help()

        if self.has_access():
            my_ret_val, my_ret_mesg = self.action(a_params)
        else:
            my_ret_val = False
            my_ret_mesg = "Error: cmd access denied"

            my_audit = Audit()
            my_audit.status = "NOK"
            my_audit.category = "CMD"
            if current_user.is_anonymous:
                my_audit.by_user = "Anonymous"
            else:
                my_audit.by_user = current_user.email

            my_audit.description = "access denied cmd"
            get_db().session.add(my_audit)
            get_db().session.commit()

        if my_ret_mesg == '..':
            my_ret_val = True
            my_ret_mesg = ''

        return my_ret_val, my_ret_mesg

    def action(self, a_params: list):
        # placeholder for the real action
        pass

    def help(self, a_wrapped=True):
        # placeholder for teal help
        pass
