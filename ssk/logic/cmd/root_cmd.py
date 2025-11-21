#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#

from .admin_cmd import AdminCmd
from .abstract_cmd import AbstractCmd
from flask_login import current_user

from ...db import get_db
from ...models.audit import Audit


class RootCmd(AbstractCmd):
    def __init__(self, a_name="."):
        super().__init__(a_name)
        self.reg_cmd(["a", "admin"], AdminCmd())

    def action(self, a_params):
        my_ret_val = False
        my_ret_mesg = ""

        my_cmd_name = a_params.pop(0)
        my_cmd = self.get_cmd(my_cmd_name)
        if my_cmd is not None:
            my_ret_val, my_ret_mesg = my_cmd.exec(a_params)

            my_audit = Audit()
            my_audit.category = "CMD"
            my_audit.by_user = current_user.email
            my_audit.description = "{} {}: {}".format(my_cmd_name, " ".join(a_params), my_ret_val)

            if my_ret_val:
                my_audit.status = "OK"
            else:
                my_audit.status = "NOK"

            get_db().session.add(my_audit)
            get_db().session.commit()

        return my_ret_val, my_ret_mesg

    def help(self, a_wrapped=True):
        my_names = []
        my_mesg = '[[ print "'
        for my_tmp_cmd in self.get_all_cmds().values():
            my_name = my_tmp_cmd.get_name()
            if my_name not in my_names:
                my_mesg += "\n{}".format(my_name)
                my_names.append(my_name)

        my_mesg += '" ]]'

        return my_mesg
