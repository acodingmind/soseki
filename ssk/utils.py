#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


import os
import sys
from datetime import datetime

import math
from flask import current_app
from math import floor
from ssk.globals.setting_parser import SettingParser
from markupsafe import escape


def get_safe_string(a_string):
    my_ret_val = ""

    if " " in a_string or a_string.isalnum():
        my_ret_val = escape(a_string)

    return str(my_ret_val)


def set_const(an_env, a_def=None, a_type=SettingParser.STR_TYPE):
    my_ret_val = os.getenv(an_env, None)
    if my_ret_val is None:
        if a_def is None:
            print("{} not found".format(an_env))
            sys.exit(1)
        else:
            #print("{} env var not found, setting from config file {}".format(an_env, a_def))
            my_ret_val = a_def
    else:
        print("{} env var overwrites config file value".format(an_env))

    my_ret_val = SettingParser.parse(a_type, my_ret_val)

    return my_ret_val


def get_padding(a_str, a_padding):
    if a_str is None:
        a_str = "-"

    my_retval = str(a_str)

    if len(my_retval) < a_padding:
        my_to_add = a_padding - len(my_retval)

        my_padding = " " * my_to_add
        my_retval = my_retval + my_padding
    else:
        my_retval = my_retval[0:a_padding-2] + "**"

    return my_retval


def get_ago(a_seconds, a_suffix="ago"):
    my_ret_val = "now"

    if a_seconds > 0:
        my_ret_val = "{} secs {}".format(a_seconds, a_suffix)
    if a_seconds > 60:
        my_ret_val = "{} mins {}".format(floor(a_seconds / 60), a_suffix)
    if a_seconds > 86400:
        my_ret_val = "{} days {}".format(floor(a_seconds / 86400), a_suffix)

    return my_ret_val


def get_timestamp_str():
    my_now = datetime.now()

    current_time = my_now.strftime("%H:%M:%S")
    return "{}".format(current_time)


def now(a_mins=0):
    from datetime import datetime, timedelta
    my_time_travel = current_app.config["TIME_TRAVEL"]
    if my_time_travel != '':
        my_ret_val = datetime.strptime(my_time_travel, "%Y-%m-%d %H:%M:%S")
    else:
        my_ret_val = datetime.now()

    if a_mins > 0:
        my_ret_val = my_ret_val - timedelta(minutes=a_mins)

    return my_ret_val


def timestamp_str():
    current_time = now().strftime("%H:%M:%S")
    return "{}".format(current_time)


def parse_time(a_time_str):
    my_ret_val = 0

    try:
        if ":" in a_time_str:
            my_split = a_time_str.split(':')
            my_min = int(my_split[0])
            my_rest = float(my_split[1])
        else:
            my_min = 0
            my_rest = float(a_time_str)

        my_ret_val = my_min * 60 + my_rest
        my_ret_val = round(my_ret_val, 3)
    except Exception as e:
        current_app.logger.error("cannot parse {} to float {}".format(a_time_str, e))

    return my_ret_val


def sec_to_str(a_time):
    my_retval = ""

    my_hr = 0
    if a_time > 3600:
        my_hr = math.floor(a_time/3600)

    my_rest = a_time - my_hr*3600
    my_min = 0
    if my_rest > 60:
        my_min = math.floor(my_rest/60)

    my_sec = round(a_time - my_hr*3600 - my_min*60, 3)

    if my_hr > 0:
        my_retval = "{}h".format(my_hr)

    if my_min > 0:
        my_retval += "{}:{}".format(my_min, my_sec)
    else:
        my_retval += "{}".format(my_sec)

    return my_retval
