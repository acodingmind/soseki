#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


import logging
from ssk.ssk_consts import SSK_VER, SSK_MODEL_VERSION, SSK_ADMIN_GROUP


def get_log_level(an_app):
    my_ret_val = logging.DEBUG
    if an_app.config["LOG_LEVEL"] == "INFO":
        my_ret_val = logging.INFO
    elif an_app.config["LOG_LEVEL"] == "WARN":
        my_ret_val = logging.WARN
    elif an_app.config["LOG_LEVEL"] == "ERROR":
        my_ret_val = logging.ERROR
    elif an_app.config["LOG_LEVEL"] == "FATAL":
        my_ret_val = logging.FATAL
    elif an_app.config["LOG_LEVEL"] == "CRITICAL":
        my_ret_val = logging.CRITICAL

    return my_ret_val


class Config(object):
    SSK_VER = SSK_VER
    SSK_DB_MODEL_VERSION = SSK_MODEL_VERSION

    # user init
    USER_GROUP_NAME = "user"
    ADMIN_GROUP_NAME = SSK_ADMIN_GROUP

    ADMIN_NAME = "admin"
    USER_FREE_NAME = "user_free"
