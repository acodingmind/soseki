#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


from sqlalchemy import desc

from .abstract_cmd import AbstractCmd
from ...models.user import User, Role
from ...utils import get_padding
from ...db import get_db


class GroupPrintCmd(AbstractCmd):
    def __init__(self):
        super().__init__("list")

    def action(self, a_param: list):
        my_mesg = '[[ print "\n'

        my_template = "{} {} {} {}\n"
        my_roles = Role.query.order_by(desc(Role.created)).all()
        my_mesg = my_mesg + my_template.format(get_padding("id", 6),
                                               get_padding("name", 10),
                                               get_padding("members", 30),
                                               get_padding("created", 20))

        my_mesg = my_mesg + my_template.format("_" * 6,
                                               "_" * 10,
                                               "_" * 30,
                                               "_" * 20)

        for my_tmp_role in my_roles:
            my_members = my_tmp_role.users
            my_mesg = my_mesg + my_template.format(get_padding(my_tmp_role.id, 6),
                                                   get_padding(my_tmp_role.name, 10),
                                                   get_padding(len(my_members), 30),
                                                   get_padding(my_tmp_role.created, 20))

            for my_tmp_member in my_members:
                my_mesg = my_mesg + my_template.format(" " * 6,
                                                       " " * 10,
                                                       get_padding(my_tmp_member.email, 30),
                                                       "  " * 20)

            my_mesg = my_mesg + my_template.format(" " * 6,
                                                   " " * 10,
                                                   " " * 30,
                                                   " " * 20)

        my_mesg = my_mesg + '" ]]'

        return True, my_mesg

    def help(self, a_wrapped=True):
        return '[[ print "Usage: group ls\nprints list of all groups" ]]'


class GroupAddCmd(AbstractCmd):
    def __init__(self):
        super().__init__("add")

    def action(self, a_params: list):
        my_ret_val = False
        my_ret_mesg = AbstractCmd.HELP_STR

        if len(a_params) == 2:
            my_user_name = a_params[0]
            my_role_name = a_params[1]

            my_role = get_db().session.query(Role).filter(Role.name == my_role_name).first()
            if my_role is not None:
                my_user = get_db().session.query(User).filter(User.email == my_user_name).first()
                if my_user is not None:
                    my_user.roles.append(my_role)

                    my_ret_val = True
                    my_ret_mesg = '[[ print "OK: {} added to {}" ]]'.format(my_role_name, my_role.name)
                else:
                    my_ret_mesg = '[[ print "Error: user {} not found" ]]'.format(my_user_name)
            else:
                my_ret_mesg = '[[ print "Error: group \'{}\' not found" ]]'.format(my_role_name)

        return my_ret_val, my_ret_mesg

    def help(self, a_wrapped=True):
        return '[[ print "Usage: group add <email> <group_name> \nadd user to a group" ]]'


class GroupDelCmd(AbstractCmd):
    def __init__(self):
        super().__init__("delete")

    def action(self, a_params: list):
        my_ret_val = False
        my_ret_mesg = AbstractCmd.HELP_STR

        if len(a_params) == 2:
            my_user_name = a_params[0]
            my_role_name = a_params[1]

            my_role = get_db().session.query(Role).filter(Role.name == my_role_name).first()
            if my_role is not None:
                my_user = get_db().session.query(User).filter(User.email == my_user_name).first()
                if my_user is not None:
                    if my_user.has_role(my_role.name):
                        my_user.roles.remove(my_role)

                        my_ret_val = True
                        my_ret_mesg = '[[ print "OK: {} removed from {}" ]]'.format(my_user_name, my_role_name)
                    else:
                        my_ret_mesg = '[[ print "Error: {} is not {}" ]]'.format(my_user_name, my_role_name)
                else:
                    my_ret_mesg = '[[ print "Error: user {} not found" ]]'.format(my_user_name)
            else:
                my_ret_mesg = '[[ print "Error: group {} not found" ]]'.format(my_role_name)

        return my_ret_val, my_ret_mesg

    def help(self, a_wrapped=True):
        return '[[ print "Usage: group del <email> <group_name> \ndelete user from a group" ]]'


class GroupNewCmd(AbstractCmd):
    def __init__(self):
        super().__init__("new")

    def action(self, a_params: list):
        my_ret_val = False
        my_ret_mesg = AbstractCmd.HELP_STR

        if len(a_params) == 1:
            my_role_name = a_params[0]

            my_role = get_db().session.query(Role).filter(Role.name == my_role_name).first()
            if my_role is None:
                my_new_role = Role()
                my_new_role.name = my_role_name

                get_db().session.add(my_new_role)
                get_db().session.commit()

                my_ret_val = True
                my_ret_mesg = '[[ print "OK: group \'{}\' created" ]]'.format(my_role_name)
            else:
                my_ret_mesg = '[[ print "Error: group \'{}\' already exists" ]]'.format(my_role_name)

        return my_ret_val, my_ret_mesg

    def help(self, a_wrapped=True):
        return '[[ print "Usage: group new <group_name> \ncreates new user group" ]]'


class GroupCmd(AbstractCmd):
    def __init__(self):
        super().__init__("groups")
        self.reg_cmd(["l", "list"], GroupPrintCmd())
        self.reg_cmd(["n", "new"], GroupNewCmd())
        self.reg_cmd(["a", "add"], GroupAddCmd())
        self.reg_cmd(["d", "delete"], GroupDelCmd())

    def action(self, a_params: list):
        my_result = False
        my_mesg = self.help()

        my_cmd_name = self.get_params(a_params)
        my_cmd = self.get_cmd(my_cmd_name)
        if my_cmd is not None:
            my_result, my_mesg = my_cmd.exec(a_params)

        return my_result, my_mesg

    def help(self, a_wrapped=True):
        return '[[ print "Usage: groups {list | new | add | delete}" ]]'
