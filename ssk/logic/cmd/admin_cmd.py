#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


from .abstract_cmd import AbstractCmd
from .health_cmd import HealthCmd
from .job_cmd import JobCmd
from .page_stat_cmd import PageStatCmd
from .db_stat_cmd import DbStatCmd
from .db_cleanup_cmd import DbCleanupCmd
from .tail_cmd import TailCmd
from .config_cmd import ConfigCmd
from .api_cmd import ApiCmd
from .user_cmd import UserCmd
from .group_cmd import GroupCmd
from .change_pass_cmd import ChangePasswdCmd
from .mail_cmd import MailCmd
from .validate_cmd import ValidateUserCmd
from flask_login import current_user

from ...db import get_db
from ...models.audit import Audit


class AdminCmd(AbstractCmd):
    def __init__(self, a_name="admin"):
        super().__init__(a_name)
        self.reg_cmd(["a", "api"], ApiCmd())
        self.reg_cmd(["c", "conf"], ConfigCmd())
        self.reg_cmd(["g", "group"], GroupCmd())
        self.reg_cmd(["h", "health"], HealthCmd())
        self.reg_cmd(["j", "jobs"], JobCmd())
        self.reg_cmd(["m", "mai;"], MailCmd())
        self.reg_cmd(["p", "passwd"], ChangePasswdCmd())
        self.reg_cmd(["s", "stats"], PageStatCmd())
        self.reg_cmd(["dbst", "dbstats"], DbStatCmd())
        self.reg_cmd(["dbcl", "dbcleanup"], DbCleanupCmd())
        self.reg_cmd(["t", "tail"], TailCmd())
        self.reg_cmd(["u", "user"], UserCmd())
        self.reg_cmd(["v", "verify"], ValidateUserCmd())

    def action(self, a_params):
        my_ret_mesg = self.help()

        my_cmd_name = self.get_params(a_params)
        my_ret_val = (my_cmd_name == "?")
        my_cmd = self.get_cmd(my_cmd_name)
        if my_cmd is not None:
            my_audit = Audit()
            my_params_str = " ".join(a_params)
            my_ret_val, my_ret_mesg = my_cmd.exec(a_params)

            my_audit.category = "CMD"
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
        my_mesg = '[[ print "---\n'
        for my_tmp_cmd in self.get_all_cmds().values():
            my_name = my_tmp_cmd.get_name()
            if my_name not in my_names:
                my_mesg += "{}\n".format(my_name)
                my_names.append(my_name)

        my_mesg += '" ]]'

        return my_mesg
