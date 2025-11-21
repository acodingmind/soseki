#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


import os

import psutil

from flask import current_app
import json

from ssk.globals.api_gate import ApiGate
from ssk.utils import get_safe_string


class ApiHandler(object):
    API_ERROR_TEMPLATE = "%s key %s version %s code %s message %s"

    @staticmethod
    def status(a_version, a_key):
        my_response = ApiGate.TOO_BUSY
        my_mesg = ""
        my_ret_val = 400

        if ApiGate.is_active_now(a_key):
            my_mesg = ApiGate.DONE
            my_ret_val = 200
        elif ApiGate.num_active_keys() < current_app.config["MAX_ACTIVE_KEYS"]:
            # this call works even if api is closed
            if ApiGate.is_valid(current_app, a_key, ignore_open=True):
                my_mesg = ApiGate.DONE
                my_ret_val = 200
            else:
                my_mesg = ApiGate.INVALID_KEY

        if my_ret_val == 200:
            my_process = psutil.Process(os.getpid())
            my_mem = round(my_process.memory_info().rss / (1024 ** 2), 2)
            my_data = {"mem": my_mem}

            my_response = json.dumps(my_data)
        else:
            current_app.logger.error(ApiHandler.API_ERROR_TEMPLATE, "status",
                                     get_safe_string(a_key),
                                     get_safe_string(a_version),
                                     my_ret_val,
                                     get_safe_string(my_mesg))

        return my_response, my_ret_val

    @staticmethod
    def echo(a_request, a_version, a_key):
        my_response = ApiGate.TOO_BUSY
        my_mesg = ""
        my_ret_val = 400

        if ApiGate.is_active_now(a_key):
            my_mesg = ApiGate.DONE
            my_ret_val = 200
        elif ApiGate.num_active_keys() < current_app.config["MAX_ACTIVE_KEYS"]:
            if ApiGate.is_valid(current_app, a_key):
                my_mesg = ApiGate.DONE
                my_ret_val = 200
            else:
                my_mesg = ApiGate.INVALID_KEY

        if my_ret_val == 200:
            my_content = a_request.json

            my_response = "I can't hear you"
            if "echo" in my_content.keys():
                my_response = get_safe_string(my_content["echo"])
        else:
            current_app.logger.error(ApiHandler.API_ERROR_TEMPLATE, "echo",
                                     get_safe_string(a_key),
                                     get_safe_string(a_version),
                                     my_ret_val,
                                     get_safe_string(my_mesg))

        return my_response, my_ret_val
