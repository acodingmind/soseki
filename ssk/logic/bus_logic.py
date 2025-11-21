#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#

from .cmd.root_cmd import RootCmd
from ..globals.job_mgr import JobMgr


class BusLogic:
    _job_mgr = None

    @staticmethod
    def get_instance():
        return BusLogic()

    def get_id(self):
        # this is default logic
        return 0

    def __init__(self):
        self._job_mgr = JobMgr()

    def get_job_mgr(self):
        return self._job_mgr

    def get_root_cmd(self):
        return RootCmd()

