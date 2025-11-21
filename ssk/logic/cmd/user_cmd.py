#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


from flask import current_app
from sqlalchemy import desc

from .abstract_cmd import AbstractCmd
from ...models.user import User
from ...utils import get_padding, get_ago
from ...db import get_db
from datetime import datetime


class UserDisableCmd(AbstractCmd):
    def __init__(self):
        super().__init__("disable")

    def action(self, a_params: list):
        my_ret_val = False
        my_ret_mesg = self.help()

        if len(a_params) == 1:
            if a_params[0] == "all":
                my_users = get_db().session.query(User).filter(User.username != current_app.config["ADMIN_NAME"]).all()

                for my_tmp_user in my_users:
                    my_tmp_user.active = False
                    get_db().session.add(my_tmp_user)

                get_db().session.commit()

                my_ret_val = True
                my_ret_mesg = '[[ print "OK: all non admin users disabled" ]]'
            else:
                my_user = User.get_by_email(a_params[0])

                if my_user is not None:
                    my_user.active = False

                    get_db().session.add(my_user)
                    get_db().session.commit()

                    my_ret_val = True
                    my_ret_mesg = '[[ print "OK: user {} disabled" ]]'.format(a_params[0])
                else:
                    my_ret_mesg = UserCmd.ERROR_USER_NOT_FOUND.format(a_params[0])

        return my_ret_val, my_ret_mesg

    def help(self, a_wrapped=True):
        return '[[ print "Usage: users off [<email>|all]\ndisable a user" ]]'


class UserRemoveCmd(AbstractCmd):
    def __init__(self):
        super().__init__("del")

    def action(self, a_params: list):
        my_ret_val = False
        my_ret_mesg = self.help()

        if len(a_params) == 1:
            my_user = User.get_by_email(a_params[0])

            if my_user is not None:
                if not my_user.active:
                    get_db().session.delete(my_user)
                    get_db().session.commit()

                    my_ret_val = True
                    my_ret_mesg = '[[ print "OK: user {} removed" ]]'.format(a_params[0])
                else:
                    my_ret_mesg = '[[ print "Error: Cannot remove active user {}" ]]'.format(a_params[0])
            else:
                my_ret_mesg = UserCmd.ERROR_USER_NOT_FOUND.format(a_params[0])

        return my_ret_val, my_ret_mesg

    def help(self, a_wrapped=True):
        return '[[ print "Usage: users del <email>\nremove a user" ]]'


class UserEnableCmd(AbstractCmd):
    def __init__(self):
        super().__init__("enable")

    def action(self, a_params: list):
        my_ret_val = False
        my_ret_mesg = self.help()

        if len(a_params) == 1:
            if a_params[0] == "all":
                my_users = get_db().session.query(User).filter(User.username != current_app.config["ADMIN_NAME"]).all()

                for my_tmp_user in my_users:
                    my_tmp_user.active = True
                    get_db().session.add(my_tmp_user)

                get_db().session.commit()

                my_ret_val = True
                my_ret_mesg = '[[ print "OK: all non admin users enabled" ]]'
            else:
                my_user = User.get_by_email(a_params[0])
                if my_user is not None:
                    my_user.active = True

                    get_db().session.add(my_user)
                    get_db().session.commit()

                    my_ret_val = True
                    my_ret_mesg = '[[ print "OK: user {} enabled" ]]'.format(a_params[0])
                else:
                    my_ret_mesg = UserCmd.ERROR_USER_NOT_FOUND.format(a_params[0])

        return my_ret_val, my_ret_mesg

    def help(self, a_wrapped=True):
        return '[[ print "Usage: users on [<email>|all]\nenable a user" ]]'


class UserPrintCmd(AbstractCmd):
    def __init__(self):
        super().__init__("list")

    def action(self, a_param: list):
        my_mesg = '[[ print "\n'

        my_template = "{} {} {} {} {} {} {} {} {} {} {}\n"
        my_users = User.query.order_by(desc(User.created)).all()
        my_mesg = my_mesg + my_template.format(get_padding("id", 6),
                                               get_padding("username", 10),
                                               get_padding("groups", 20),
                                               get_padding("subs", 10),
                                               get_padding("on", 4),
                                               get_padding("email", 30),
                                               get_padding("last login", 12),
                                               get_padding("active", 12),
                                               get_padding("#", 4),
                                               get_padding("registered", 20),
                                               get_padding("confirmed", 30))

        my_mesg = my_mesg + my_template.format("_" * 6,
                                               "_" * 10,
                                               "_" * 20,
                                               "_" * 10,
                                               "_" * 4,
                                               "_" * 30,
                                               "_" * 12,
                                               "_" * 12,
                                               "_" * 4,
                                               "_" * 20,
                                               "_" * 30)

        for my_tmp_user in my_users:
            my_roles = (myTmpRole.name for myTmpRole in my_tmp_user.roles)
            my_roles_str = ", ".join(my_roles)

            my_subs = (myTmpSub.name for myTmpSub in my_tmp_user.subs)
            my_subs_str = ", ".join(my_subs)

            my_on = "ON"
            if not my_tmp_user.active:
                my_on = "OFF"

            my_last_login_str = "-"
            if my_tmp_user.last_login is not None:
                my_last_login_str = get_ago((datetime.now() - my_tmp_user.last_login).seconds)

            my_last_access_str = "-"
            if my_tmp_user.last_access is not None:
                my_last_access_str = get_ago((datetime.now() - my_tmp_user.last_access).seconds)

            confirmed_str = "-"
            if my_tmp_user.email_confirmed_at is not None:
                confirmed_str = get_ago((my_tmp_user.email_confirmed_at - my_tmp_user.created).seconds,
                                        a_suffix="later")

            my_mesg = my_mesg + my_template.format(get_padding(my_tmp_user.id, 6),
                                                   get_padding(my_tmp_user.username, 10),
                                                   get_padding(my_roles_str, 20),
                                                   get_padding(my_subs_str, 10),
                                                   get_padding(my_on, 4),
                                                   get_padding(my_tmp_user.email, 30),
                                                   get_padding(my_last_login_str, 12),
                                                   get_padding(my_last_access_str, 12),
                                                   get_padding(my_tmp_user.num_of_logins, 4),
                                                   get_padding(my_tmp_user.created, 20),
                                                   get_padding(confirmed_str, 30))

        my_mesg = my_mesg + '" ]]'

        return True, my_mesg

    def help(self, a_wrapped=True):
        return '[[ print "Usage: user ls\nprints the list of all users" ]]'


class UserCmd(AbstractCmd):
    ERROR_USER_NOT_FOUND = '[[ print "Error: User {} not found" ]]'

    def __init__(self):
        super().__init__("user")
        self.reg_cmd(["l", "list"], UserPrintCmd())
        self.reg_cmd(["e", "enable"], UserEnableCmd())
        self.reg_cmd(["d", "disable"], UserDisableCmd())
        self.reg_cmd(["r", "remove"], UserRemoveCmd())

    def action(self, a_params: list):
        my_result = False
        my_mesg = self.help()

        my_cmd_name = self.get_params(a_params)
        my_cmd = self.get_cmd(my_cmd_name)
        if my_cmd is not None:
            my_result, my_mesg = my_cmd.exec(a_params)

        return my_result, my_mesg

    def help(self, a_wrapped=True):
        return '[[ print "Usage: user {list | enable | disable | remove}" ]]'
