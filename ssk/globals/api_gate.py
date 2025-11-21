#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


from time import time
import json
import uuid

from ..globals.app_settings import AppSettings
from ..models.apikey import ApiKey
from ..utils import get_safe_string


class ApiGate:
    DONE = json.dumps({"code": 0, "mesg": "ok"})
    INVALID_KEY = json.dumps({"code": 10, "mesg": "invalid api key"})
    TOO_BUSY = json.dumps({"code": 20, "mesg": "maximum active sessions exceeded"})
    CLOSED = json.dumps({"code": 30, "mesg": "API is temporarily disabled"})

    __allowed = None
    __active = None
    __timeout = None
    __open = False

    @staticmethod
    def init():
        my_app_settings = AppSettings()

        ApiGate.__timeout = my_app_settings.get_setting("API_ACTIVE_NOW")
        ApiGate.__active = {}
        ApiGate.__allowed = {}

    @staticmethod
    def load():
        my_keys = ApiKey.get_all_active()

        ApiGate.__allowed = {}
        for my_tmp_key in my_keys:
            ApiGate.__allowed[my_tmp_key.key] = "key driver {}".format(my_tmp_key.id)

    @staticmethod
    def get_new_key():
        my_ret_val = str(uuid.uuid4())

        return my_ret_val

    @staticmethod
    def add_api_key(a_user_email):
        my_ret_val = None
        from ssk.models.user import User

        my_user = User.get_by_email(a_user_email)
        if my_user is not None:
            from ssk.db import get_db

            my_api_key = ApiKey()
            my_api_key.owner = my_user
            my_api_key.key = ApiGate.get_new_key()
            get_db().session.add(my_api_key)
            get_db().session.commit()

            ApiGate.load()
            my_ret_val = my_api_key.key

        return my_ret_val

    @staticmethod
    def active_now():
        my_now = time()
        my_threshold = my_now - ApiGate.__timeout

        my_values = ApiGate.__active.values()
        my_active = list(filter(lambda my_key: my_key > my_threshold, my_values))

        return my_active

    @staticmethod
    def is_active_now(a_key):
        my_retval = False

        if ApiGate.__active is not None and a_key in ApiGate.__active.keys():
            my_ts = ApiGate.__active[a_key]
            my_retval = (my_ts > time() - ApiGate.__timeout)

        if my_retval:
            ApiGate.__active[a_key] = time()

        return my_retval

    @staticmethod
    def num_active_keys():
        if ApiGate.__active is None:
            return 0

        return len(ApiGate.active_now())

    @staticmethod
    def num_total_keys():
        if ApiGate.__allowed is None:
            return 0

        return len(ApiGate.__allowed.keys())

    @staticmethod
    def set_open(a_flag):
        ApiGate.__open = a_flag

    @staticmethod
    def is_open():
        return ApiGate.__open

    @staticmethod
    def is_valid(an_app, a_key, ignore_open=False):
        my_ret_val = False

        if ApiGate.is_open() or ignore_open:
            if ApiGate.__allowed is not None:
                my_ret_val = a_key in ApiGate.__allowed.keys()

                if my_ret_val:
                    ApiGate.__active[a_key] = time()

            if not my_ret_val:
                an_app.logger.info("api key rejected %s", get_safe_string(a_key))
            else:
                an_app.logger.debug("api key accepted %s", get_safe_string(a_key))
        else:
            an_app.logger.debug("api is closed")

        return my_ret_val
