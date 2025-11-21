#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#
from flask import current_app

from ssk.globals.setting_parser import SettingParser
from ssk.globals.app_settings import AppSettings


def test_parse(app):
    with app.app_context():
        assert SettingParser.parse(SettingParser.STR_TYPE, "AAA") == "AAA"
        assert SettingParser.parse(SettingParser.STR_TYPE, "1.01") == "1.01"
        assert SettingParser.parse(SettingParser.FLT_TYPE, 1.01) == 1.01
        assert SettingParser.parse(SettingParser.FLT_TYPE, "1.01") == 1.01
        assert SettingParser.parse(SettingParser.FLT_TYPE, "A") is None
        assert not SettingParser.parse(SettingParser.BOOL_TYPE, "AAA")
        assert SettingParser.parse(SettingParser.BOOL_TYPE, "True")


def test_get_def_settings(app):
    with app.app_context():

        my_sut = AppSettings()
        assert my_sut.get_setting("MAX_COLLECTORS") == current_app.config["MAX_COLLECTORS"]
        assert my_sut.get_setting("MAX_ACTIVE_KEYS") == current_app.config["MAX_ACTIVE_KEYS"]
        assert my_sut.get_setting("API_ACTIVE_NOW") == current_app.config["API_ACTIVE_NOW"]


def test_setting_mgmt(app):
    with app.app_context():
        my_sut = AppSettings()

        my_admin_email = app.config["ADMIN_EMAIL"]
        my_setting_key = "SOME_KEY"
        my_setting_val = "ABC"
        assert my_sut.set_setting(my_admin_email, my_setting_key, SettingParser.STR_TYPE, my_setting_val)
        assert my_sut.get_setting(my_setting_key, my_admin_email) == my_setting_val
        assert my_sut.del_setting(my_admin_email, my_setting_key)
        assert my_sut.get_setting(my_setting_key, my_admin_email) is None

        # set global
        assert my_sut.set_setting(my_admin_email, my_setting_key, SettingParser.STR_TYPE, my_setting_val)
        assert my_sut.set_global(my_setting_key, True)
        assert my_sut.set_global(my_setting_key, False)


