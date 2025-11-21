#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


from flask_login import current_user

from .abstract_cmd import AbstractCmd
from ... import get_db
from ...models.audit import Audit
from ...utils import get_padding


class IntroCmd(AbstractCmd):
    def __init__(self):
        super().__init__("(w)hy", a_type=AbstractCmd.ANON)

    def action(self, a_param: list):
        my_mesg = '[[ print "'
        my_mesg += "\nsoseki.io has a command line interface because cmd can be extended quickly with a minimum risk of regression.\nThis way features can be delivered faster, and extended with a better GUI afterwards when real user feedback is available.\n"
        my_mesg = my_mesg + '" ]]'

        return True, my_mesg

    def help(self, a_wrapped=True):
        my_help = "why cmd in a web based tool ?"
        if a_wrapped:
            my_help = '[[ print "Usage: ?\n{}" ]]'.format(my_help)

        return my_help


class AnonCmd(AbstractCmd):
    def __init__(self):
        super().__init__("anon", a_type=AbstractCmd.ANON)
        self.reg_cmd(["w", "why"], IntroCmd())

    def action(self, a_params):
        my_ret_val = False
        my_ret_mesg = self.help()

        if len(a_params) > 0:
            my_cmd_name = self.get_params(a_params)
            my_cmd = self.get_cmd(my_cmd_name)
            if my_cmd is not None:
                my_audit = Audit()

                my_params_str = " ".join(a_params)
                my_ret_val, my_ret_mesg = my_cmd.exec(a_params)

                my_audit.category = "CMD"
                if current_user.is_anonymous:
                    my_audit.by_user = "anonymous"
                else:
                    my_audit.by_user = current_user.email
                my_audit.description = "{} {}: {}".format(my_cmd_name, my_params_str, my_ret_val)

                if my_ret_val:
                    my_audit.status = "OK"
                else:
                    my_audit.status = "NOK"
                get_db().session.add(my_audit)
                get_db().session.commit()

        return my_ret_val, my_ret_mesg

    def help(self, a_wrapped=True):
        my_names = []
        my_mesg = '[[ print "supported commands:'

        for my_tmp_cmd in self.get_all_cmds().values():
            my_name = my_tmp_cmd.get_name()
            if my_name not in my_names:
                my_mesg += "\n{} : {}".format(get_padding(my_name, 10), my_tmp_cmd.help(False))
                my_names.append(my_name)

        my_mesg += '\n" ]]'

        return my_mesg
