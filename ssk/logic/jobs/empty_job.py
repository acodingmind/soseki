#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#

import time

from .base_job import BaseJob


class EmptyJob(BaseJob):
    def __init__(self, an_app, a_args):
        super(EmptyJob, self).__init__(an_app, a_args)

    def work(self):
        my_total = 60

        for my_tmp_idx in range(1, my_total):
            time.sleep(1)
            self.set_progress(a_val=round((my_tmp_idx / my_total) * 100))