#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


import json

from flask import current_app

from .abstract_cmd import AbstractCmd
from ...models.setting import Setting
from ...utils import get_padding
from ...globals.app_settings import AppSettings
from ...globals.app_settings import SettingParser


class ConfigConstsCmd(AbstractCmd):
    def __init__(self):
        super().__init__("consts")

    def action(self, a_params: list):
        my_retval = True
        my_mesg = '[[ print "\n'

        my_template = "{} {}\n"
        my_mesg = my_mesg + my_template.format(get_padding("name", 20),
                                               get_padding("value", 50))

        my_mesg = my_mesg + my_template.format("_" * 20, "_" * 50)

        my_mesg = my_mesg + my_template.format(get_padding("MAIL_USERNAME", 20), current_app.config["MAIL_USERNAME"])
        my_mesg = my_mesg + my_template.format(get_padding("MAIL_PASSWORD", 20), current_app.config["MAIL_PASSWORD"])
        my_mesg = my_mesg + my_template.format(get_padding("MAIL_SUPPRESS_SEND", 20),
                                               current_app.config["MAIL_SUPPRESS_SEND"])

        my_mesg = my_mesg + my_template.format(get_padding("MAX_COLLECTORS", 20), current_app.config["MAX_COLLECTORS"])
        my_mesg = my_mesg + my_template.format(get_padding("MAX_ACTIVE_KEYS", 20),
                                               current_app.config["MAX_ACTIVE_KEYS"])
        my_mesg = my_mesg + my_template.format(get_padding("API_ACTIVE_NOW", 20), current_app.config["API_ACTIVE_NOW"])

        my_mesg = my_mesg + '" ]]'

        return my_retval, my_mesg

    def help(self, a_wrapped=True):
        return '[[ print "Usage: conf consts\nprints all constants" ]]'


class ConfigPrintCmd(AbstractCmd):
    def __init__(self):
        super().__init__("list")

    def action(self, a_params: list):
        my_retval = True
        my_mesg = '[[ print "\n'

        my_template = "{} {} {} {} {} {}\n"
        my_settings = Setting.query.all()
        my_mesg = my_mesg + my_template.format(get_padding("key", 20),
                                               get_padding("owner", 30),
                                               get_padding("global", 7),
                                               get_padding("type", 7),
                                               get_padding("updated", 20),
                                               get_padding("created", 20)
                                               )

        my_mesg = my_mesg + my_template.format("_" * 20,
                                               "_" * 30,
                                               "_" * 7,
                                               "_" * 7,
                                               "_" * 20,
                                               "_" * 20)

        for my_tmp_setting in my_settings:
            my_mesg = my_mesg + my_template.format(get_padding(my_tmp_setting.key, 20),
                                                   get_padding(my_tmp_setting.owner.email, 30),
                                                   get_padding(my_tmp_setting.system, 7),
                                                   get_padding(my_tmp_setting.type, 7),
                                                   get_padding(my_tmp_setting.updated, 20),
                                                   get_padding(my_tmp_setting.created, 20))

            my_value = my_tmp_setting.value
            if my_tmp_setting.type == SettingParser.JSON_TYPE:
                my_json = json.loads(my_value)
                for my_tmp_key in my_json.keys():
                    my_mesg = my_mesg + "{} {} {} : {}\n".format(" " * 20, " " * 30, my_tmp_key, my_json[my_tmp_key])
            else:
                my_mesg = my_mesg + "{} {} {}\n".format(" " * 20, " " * 30, get_padding(my_value, 100))

            my_mesg = my_mesg + "\n"

        my_mesg = my_mesg + '" ]]'

        return my_retval, my_mesg

    def help(self, a_wrapped=True):
        return '[[ print "Usage: conf ls\nprints all settings" ]]'


class ConfigGlobalCmd(AbstractCmd):
    def __init__(self):
        super().__init__("global")

    def action(self, a_params: list):
        my_ret_val = False
        my_ret_mesg = AbstractCmd.HELP_STR

        if len(a_params) == 2:
            my_key = a_params[0]
            my_on = a_params[1]

            my_global = False
            if my_on == "on":
                my_global = True

            my_ret_val, my_ret_mesg = AppSettings().set_global(my_key, my_global)

        return my_ret_val, my_ret_mesg

    def help(self, a_wrapped=True):
        return '[[ print "Usage: conf glb <key> [on | off]\nmakes a setting global" ]]'


class ConfigSetCmd(AbstractCmd):
    def __init__(self):
        super().__init__("set")

    def action(self, a_params: list):
        my_ret_val = False
        my_ret_mesg = AbstractCmd.HELP_STR

        if len(a_params) == 4:
            my_user = a_params[0]
            my_type = a_params[1]
            my_key = a_params[2]
            my_value = a_params[3]

            my_ret_val, my_ret_mesg = AppSettings().set_setting(my_user, my_key, my_type, my_value)

        return my_ret_val, my_ret_mesg

    def help(self, a_wrapped=True):
        return '[[ print "Usage: conf set <email> <type> <key> <value>\nsets or adds a setting for a given user" ]]'


class ConfigGetCmd(AbstractCmd):
    def __init__(self):
        super().__init__("get")

    def action(self, a_params: list):
        my_ret_val = False
        my_ret_mesg = AbstractCmd.HELP_STR

        if len(a_params) == 2:
            my_key = a_params[0]
            my_user = a_params[1]

            my_result = AppSettings().get_setting(my_key, my_user)
            my_ret_val = True
            my_ret_mesg = '[[ print "{} for {} = {}" ]]'.format(my_key, my_user, my_result)

        if len(a_params) == 1:
            my_key = a_params[0]

            my_result = AppSettings().get_setting(my_key)

            my_ret_val = True
            my_ret_mesg = '[[ print "{} = {}" ]]'.format(my_key, my_result)

        return my_ret_val, my_ret_mesg

    def help(self, a_wrapped=True):
        return '[[ print "Usage: conf get <key> <email>\ngets a setting for a given user" ]]'


class ConfigDelCmd(AbstractCmd):
    def __init__(self):
        super().__init__("delete")

    def action(self, a_params: list):
        my_ret_val = False
        my_ret_mesg = AbstractCmd.HELP_STR

        if len(a_params) == 2:
            my_user = a_params[0]
            my_key = a_params[1]

            my_ret_val, my_ret_mesg = AppSettings().del_setting(my_user, my_key)

        return my_ret_val, my_ret_mesg

    def help(self, a_wrapped=True):
        return '[[ print "Usage: conf del <email> <key>\ndeletes a setting for a given user" ]]'


class ConfigCmd(AbstractCmd):
    def __init__(self):
        super().__init__("config")
        self.reg_cmd(["l", "list"], ConfigPrintCmd())
        self.reg_cmd(["c", "consts"], ConfigConstsCmd())
        self.reg_cmd(["s", "set"], ConfigSetCmd())
        self.reg_cmd(["g", "get"], ConfigGetCmd())
        self.reg_cmd(["d", "delete"], ConfigDelCmd())
        self.reg_cmd(["gl", "global"], ConfigGlobalCmd())

    def action(self, a_params: list):
        my_result = False
        my_mesg = self.help()

        my_cmd_name = self.get_params(a_params)
        my_cmd = self.get_cmd(my_cmd_name)
        if my_cmd is not None:
            my_result, my_mesg = my_cmd.exec(a_params)

        return my_result, my_mesg

    def help(self, a_wrapped=True):
        return '[[ print "Usage: conf {list | consts | set | get | delete | global }" ]]'
