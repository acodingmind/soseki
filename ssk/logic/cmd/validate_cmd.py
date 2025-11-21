#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


from flask import current_app


from .abstract_cmd import AbstractCmd
from ...models.user import User


class ValidateUserCmd(AbstractCmd):
    def __init__(self):
        super().__init__("verify")

    def action(self, a_params: list):
        my_ret_val = False
        my_ret_mesg = ""

        if len(a_params) == 2:
            my_user = User.get_by_email(a_params[0])

            if my_user is not None:
                my_pass = a_params[1]
                user_manager = current_app.user_manager
                if user_manager.verify_password(my_pass, my_user.password):
                    my_ret_val = True
                    my_ret_mesg = '[[ print "OK: {} password match" ]]'.format(a_params[0])
                else:
                    my_ret_mesg = '[[ print "Error: {} password invalid" ]]'.format(a_params[0])
            else:
                my_ret_mesg = '[[ print "Error: user {} not found" ]]'.format(a_params[0])

        return my_ret_val, my_ret_mesg

    def help(self, a_wrapped=True):
        return '[[ print "Usage: verify <email> <password>\nverify user password" ]]'
