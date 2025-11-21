#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


from sqlalchemy import desc

from .abstract_cmd import AbstractCmd
from ...models.apikey import ApiKey
from ...globals.api_gate import ApiGate
from ...utils import get_padding
from ...models.user import User
from ...db import get_db


class ApiPrintCmd(AbstractCmd):
    def __init__(self):
        super().__init__("list")

    def action(self, a_param: list):
        my_ret_val = True
        my_mesg = '[[ print "\n'

        my_status = "OPEN"
        if not ApiGate.is_open():
            my_status = "CLOSED"

        my_template = "{} {} {} {} {}\n"
        my_apis = ApiKey.query.order_by(desc(ApiKey.created)).all()
        my_mesg = my_mesg + "API gate:     {}\n#active keys: {} of {} total {}\n\n".format(my_status,
                                                                                           len(ApiGate.active_now()),
                                                                                           ApiGate.num_total_keys(),
                                                                                           len(my_apis))

        my_mesg = my_mesg + my_template.format(get_padding("db id", 6),
                                               get_padding("owner", 30),
                                               get_padding("key", 40),
                                               get_padding("active", 7),
                                               get_padding("created", 20))
        my_mesg = my_mesg + my_template.format("_" * 6,
                                               "_" * 30,
                                               "_" * 40,
                                               "_" * 7,
                                               "_" * 20)

        for my_tmp_api in my_apis:
            my_mesg = my_mesg + my_template.format(get_padding(my_tmp_api.id, 6),
                                                   get_padding(my_tmp_api.owner.email, 30),
                                                   get_padding(my_tmp_api.key, 40),
                                                   get_padding(my_tmp_api.active, 7),
                                                   get_padding(my_tmp_api.created, 20))

        my_mesg = my_mesg + '" ]]'

        return my_ret_val, my_mesg

    def help(self, a_wrapped=True):
        return '[[ print "Usage: api ls\nprints the list of all api keys" ]]'


class ApiOpenCmd(AbstractCmd):
    def __init__(self):
        super().__init__("open")

    def action(self, a_param: list):
        ApiGate.set_open(True)

        return True, '[[ print "OK: api is now open" ]]'

    def help(self, a_wrapped=True):
        return '[[ print "Usage: api open\nopens API Gate" ]]'


class ApiCloseCmd(AbstractCmd):
    def __init__(self):
        super().__init__("close")

    def action(self, a_param: list):
        ApiGate.set_open(False)

        return True, '[[ print "OK: api closed" ]]'

    def help(self, a_wrapped=True):
        return '[[ print "Usage: api close\ncloses API Gate" ]]'


class ApiAddCmd(AbstractCmd):
    def __init__(self):
        super().__init__("add")

    def action(self, a_params: list):
        my_ret_val = False
        my_ret_mesg = self.help()
        if len(a_params) == 1:
            my_user = User.get_by_email(a_params[0])

            if my_user is not None:
                ApiGate.add_api_key(a_params[0])

                my_ret_val = True
                my_ret_mesg = '[[ print "OK: api key added to {}" ]]'.format(a_params[0])
            else:
                my_ret_mesg = '[[ print "Error: User {} not found" ]]'.format(a_params[0])

        return my_ret_val, my_ret_mesg

    def help(self, a_wrapped=True):
        return '[[ print "Usage: api add <email>\nadds an active api key for a user" ]]'


class ApiDisableCmd(AbstractCmd):
    def __init__(self):
        super().__init__("off")

    def action(self, a_params: list):
        my_ret_val = False
        my_ret_mesg = self.help()

        if len(a_params) == 1:
            my_key = a_params[0]
            my_api_key = ApiKey.get_by_key(my_key)

            if my_api_key is not None:
                my_api_key.active = False
                get_db().session.add(my_api_key)
                get_db().session.commit()
                ApiGate.load()

                my_ret_val = True
                my_ret_mesg = '[[ print "OK: api key {} disabled" ]]'.format(a_params[0])
            else:
                my_ret_mesg = '[[ print "Error: key {} not found" ]]'.format(a_params[0])

        return my_ret_val, my_ret_mesg

    def help(self, a_wrapped=True):
        return '[[ print "Usage: api off <key>\ndisables an api key" ]]'


class ApiEnableCmd(AbstractCmd):
    def __init__(self):
        super().__init__("on")

    def action(self, a_params: list):
        my_ret_val = False
        my_ret_mesg = self.help()

        if len(a_params) == 1:
            my_key = a_params[0]
            my_api_key = ApiKey.get_by_key(my_key)

            if my_api_key is not None:
                my_api_key.active = True
                get_db().session.add(my_api_key)
                get_db().session.commit()
                ApiGate.load()

                my_ret_val = True
                my_ret_mesg = '[[ print "OK: api key {} enabled" ]]'.format(a_params[0])
            else:
                my_ret_mesg = '[[ print "Error: key {} not found" ]]'.format(a_params[0])

        return my_ret_val, my_ret_mesg

    def help(self, a_wrapped=True):
        return '[[ print "Usage: api on <key>\nenables an api key" ]]'


class ApiCmd(AbstractCmd):
    def __init__(self):
        super().__init__("api")
        self.reg_cmd(["l", "list"], ApiPrintCmd())
        self.reg_cmd(["o", "open"], ApiOpenCmd())
        self.reg_cmd(["c", "close"], ApiCloseCmd())
        self.reg_cmd(["a", "add"], ApiAddCmd())
        self.reg_cmd(["d", "disable"], ApiDisableCmd())
        self.reg_cmd(["e", "enable"], ApiEnableCmd())

    def action(self, a_params: list):
        my_result = False
        my_mesg = self.help()

        my_cmd_name = self.get_params(a_params)
        my_cmd = self.get_cmd(my_cmd_name)
        if my_cmd is not None:
            my_result, my_mesg = my_cmd.exec(a_params)

        return my_result, my_mesg

    def help(self, a_wrapped=True):
        return '[[ print "Usage: api {list | open | close | add | enable | disable }" ]]'
