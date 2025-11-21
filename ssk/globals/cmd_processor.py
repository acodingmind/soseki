#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


from threading import Thread
from queue import Queue


class CmdProcessor:
    KILL_CMD = "k"
    _cmd_queue = Queue()
    _cmd_cnt = 0
    _job_mgr = None
    _logger = None
    _workers = []

    @staticmethod
    def log(a_mesg, a_level="INFO"):
        if a_level == "DEBUG":
            CmdProcessor._logger.debug(a_mesg)
        else:
            CmdProcessor._logger.info(a_mesg)

    @staticmethod
    def process_cmd(a_job_mgr, a_num, a_job_queue):
        CmdProcessor.log("starting command worker {}".format(a_num))

        while True:
            CmdProcessor.log("worker {} waiting for command".format(a_num))

            my_cmd = a_job_queue.get()

            if my_cmd == CmdProcessor.KILL_CMD:
                raise SystemExit()

            if a_job_mgr.is_queued(my_cmd.get_task_id()):
                CmdProcessor.log("worker {} processing command {}".format(a_num, my_cmd.get_task_id()))
                CmdProcessor._cmd_cnt += 1
                try:
                    a_job_mgr.start_job(my_cmd)
                except SystemExit:
                    CmdProcessor.log("worker {} processing command {} stopped".format(a_num, my_cmd.get_task_id()))
                except Exception as e:
                    CmdProcessor.log("worker {} processing command {} error {}".format(a_num, my_cmd.get_task_id(), e))

                CmdProcessor.log("worker {} processing command {} ready".format(a_num, my_cmd.get_task_id()))

            a_job_queue.task_done()

    @staticmethod
    def start(a_job_mgr, a_logger, a_max_collectors):
        CmdProcessor._job_mgr = a_job_mgr
        CmdProcessor._logger = a_logger
        CmdProcessor.log("starting")

        for my_tmp_idx in range(a_max_collectors):
            worker = Thread(target=CmdProcessor.process_cmd, args=(a_job_mgr, my_tmp_idx, CmdProcessor._cmd_queue))
            CmdProcessor._workers.append(worker)
            worker.start()

    @staticmethod
    def stop():
        for my_tmp_idx in range(len(CmdProcessor._workers)):
            CmdProcessor.log("sending kill to worker {}".format(my_tmp_idx))
            CmdProcessor._cmd_queue.put(CmdProcessor.KILL_CMD)

    @staticmethod
    def submit_cmd(a_cmd):
        CmdProcessor._job_mgr.queue_job(a_cmd)
        CmdProcessor._cmd_queue.put(a_cmd)

        return CmdProcessor._cmd_queue.qsize()

    @staticmethod
    def cmd_queue_len():
        return CmdProcessor._cmd_queue.qsize()

    @staticmethod
    def data_processed():
        return CmdProcessor._cmd_cnt
