#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


from flask import current_app


class SettingParser:
    STR_TYPE = "string"
    INT_TYPE = "int"
    FLT_TYPE = "float"
    BOOL_TYPE = "bool"
    JSON_TYPE = "json"

    ERROR_KEY_EMPTY = "Key cannot be empty"

    _valid_types = [STR_TYPE, INT_TYPE, FLT_TYPE, BOOL_TYPE, JSON_TYPE]
    _globals = {}

    @staticmethod
    def is_valid(a_type):
        return a_type in SettingParser._valid_types

    @staticmethod
    def parse(a_type, a_value):
        my_ret_val = None

        try:
            if a_type == SettingParser.STR_TYPE:
                my_ret_val = str(a_value)
            elif a_type == SettingParser.INT_TYPE:
                my_ret_val = int(a_value)
            elif a_type == SettingParser.FLT_TYPE:
                my_ret_val = float(a_value)
            elif a_type == SettingParser.BOOL_TYPE:
                my_ret_val = a_value is True or (a_value == "True") or (a_value == '1')
            elif a_type == SettingParser.JSON_TYPE:
                my_ret_val = a_value
            else:
                current_app.logger.error("Unknown setting type {} for {}".format(a_type, a_value))
        except Exception:
            my_mesg = "Cannot parse type {} for {}".format(a_type, a_value)
            current_app.logger.error(my_mesg)

        return my_ret_val
    