#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


from flask import current_app

from .abstract_cmd import AbstractCmd
from ...models.user import User
from ...db import get_db, truncate_password


class ChangePasswdCmd(AbstractCmd):
    def __init__(self):
        super().__init__("passwd")

    def has_numbers(self, a_str):
        return any(char.isdigit() for char in a_str)

    def action(self, a_params: list):
        my_ret_val = False
        my_ret_mesg = self.help()

        if len(a_params) == 2:
            my_user = User.get_by_email(a_params[0])

            if my_user is not None:
                my_pass = a_params[1]

                my_pass_len = 5
                if len(my_pass) > my_pass_len and self.has_numbers(my_pass):
                    user_manager = current_app.user_manager
                    my_user.password = user_manager.hash_password(truncate_password(my_pass))

                    get_db().session.add(my_user)
                    get_db().session.commit()

                    my_ret_val = True
                    my_ret_mesg = '[[ print "OK: user {} password changed" ]]'.format(a_params[0])
                else:
                    my_ret_mesg = '[[ print "Error: password must be longer than {} and contain numbers" ]]'.format(my_pass_len)
            else:
                my_ret_mesg = '[[ print "Error: user {} not found" ]]'.format(a_params[0])

        return my_ret_val, my_ret_mesg

    def help(self, a_wrapped=True):
        return '[[ print "Usage: passwd <email> <password>\nchange password" ]]'
