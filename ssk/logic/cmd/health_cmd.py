#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


from sqlalchemy import desc

from .abstract_cmd import AbstractCmd
from ...models.status import Status
from ...utils import get_padding


class HealthCmd(AbstractCmd):
    def __init__(self):
        super().__init__("health")

    def action(self, a_param: list):
        my_mesg = ''

        if len(a_param) == 0:
            my_mesg = '[[ print "\n'

            my_template = "{} {} {} {} {} {} {} {} {} {} {} {}\n"
            my_status = Status.query.order_by(desc(Status.created)).limit(60)
            my_mesg = my_mesg + my_template.format(get_padding("api", 8),
                                                   get_padding("thr", 4),
                                                   get_padding("now", 4),
                                                   get_padding("max", 4),
                                                   get_padding("tot", 4),
                                                   get_padding("usr", 4),
                                                   get_padding("now", 4),
                                                   get_padding("cnf", 4),
                                                   get_padding("aud", 4),
                                                   get_padding("rt", 4),
                                                   get_padding("mem", 6),
                                                   get_padding("created", 20),
                                                   )

            my_mesg = my_mesg + my_template.format("_" * 8,
                                                   "_" * 4,
                                                   "_" * 4,
                                                   "_" * 4,
                                                   "_" * 4,
                                                   "_" * 4,
                                                   "_" * 4,
                                                   "_" * 4,
                                                   "_" * 4,
                                                   "_" * 4,
                                                   "_" * 6,
                                                   "_" * 20)

            for my_tmp_status in my_status:
                my_mesg = my_mesg + my_template.format(get_padding(my_tmp_status.api_status, 8),
                                                       get_padding(my_tmp_status.api_now_threshold, 4),
                                                       get_padding(my_tmp_status.api_active_now, 4),
                                                       get_padding(my_tmp_status.api_max_active, 4),
                                                       get_padding(my_tmp_status.api_total, 4),
                                                       get_padding(my_tmp_status.users, 4),
                                                       get_padding(my_tmp_status.users_active, 4),
                                                       get_padding(my_tmp_status.conf_keys, 4),
                                                       get_padding(my_tmp_status.audit_cnt, 4),
                                                       get_padding(my_tmp_status.response_time, 4),
                                                       get_padding(my_tmp_status.mem, 6),
                                                       get_padding(my_tmp_status.created, 20))

            my_mesg = my_mesg + '" ]]'
        elif a_param[0] == "h":
            my_mesg = self.help()

        return True, my_mesg

    def help(self, a_wrapped=True):
        return '[[ print "Usage: health\nprints last 60 system health snapshots" ]]'
