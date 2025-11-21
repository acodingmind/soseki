#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#
from flask import current_app

from ssk.globals.app_settings import AppSettings
from ssk.globals.setting_parser import SettingParser

from ssk import SSK_ADMIN_GROUP
from ssk.logic.cmd.config_cmd import ConfigCmd

from unittest import mock


@mock.patch('flask_login.utils._get_user')
def run_ls_conf(current_user):
    attrs = {
        'id': 1,
        'email': 'admin@soseki.io',
        'name': 'Soseki Admin',
        'roles': [SSK_ADMIN_GROUP]
    }
    current_user.return_value = mock.Mock(is_authenticated=True,
                                          is_anonymous=False, **attrs)
    current_user.return_value.is_admin.return_value = True

    my_cmd = ConfigCmd()
    my_params = ["l"]
    my_ok, my_res = my_cmd.exec(my_params)
    assert my_ok


@mock.patch('flask_login.utils._get_user')
def run_setget_conf(current_user):
    attrs = {
        'id': 1,
        'email': 'admin@soseki.io',
        'name': 'Soseki Admin',
        'roles': [SSK_ADMIN_GROUP]
    }
    my_app_settings = AppSettings()

    current_user.return_value = mock.Mock(is_authenticated=True,
                                          is_anonymous=False, **attrs)
    current_user.return_value.is_admin.return_value = True
    my_tst_email = current_app.config["USER_FREE_EMAIL"]
    my_cmd = ConfigCmd()

    my_test_str_key = "teststrkey"
    my_test_str_val = "testval"
    my_params = ["s", my_tst_email, SettingParser.STR_TYPE, my_test_str_key, my_test_str_val]
    my_ok, my_res = my_cmd.exec(my_params)
    assert my_ok
    my_setting = my_app_settings.get_setting(my_test_str_key, my_tst_email)
    assert my_setting == my_test_str_val

    my_params = ["g", my_test_str_key, my_tst_email]
    my_ok, my_res = my_cmd.exec(my_params)
    assert my_ok

    my_test_int_key = "testintkey"
    my_test_int_val = 1
    my_params = ["s", my_tst_email, SettingParser.INT_TYPE, my_test_int_key, my_test_int_val]
    my_ok, my_res = my_cmd.exec(my_params)
    assert my_ok
    my_setting = my_app_settings.get_setting(my_test_int_key, my_tst_email)
    assert my_setting == my_test_int_val

    my_test_bool_key = "testboolkey"
    my_test_bool_val = True
    my_params = ["s", my_tst_email, SettingParser.BOOL_TYPE, my_test_bool_key, my_test_bool_val]
    my_ok, my_res = my_cmd.exec(my_params)
    assert my_ok
    my_setting = my_app_settings.get_setting(my_test_bool_key, my_tst_email)
    assert my_setting == my_test_bool_val

    my_test_float_key = "testfloatkey"
    my_test_float_val = True
    my_params = ["s", my_tst_email, SettingParser.BOOL_TYPE, my_test_float_key, my_test_float_val]
    my_ok, my_res = my_cmd.exec(my_params)
    assert my_ok
    my_setting = my_app_settings.get_setting(my_test_float_key, my_tst_email)
    assert my_setting == my_test_float_val

    my_params = ["s", my_tst_email, "wrong_type", my_test_float_key, my_test_float_val]
    my_ok, my_res = my_cmd.exec(my_params)
    assert not my_ok


@mock.patch('flask_login.utils._get_user')
def run_del_conf(current_user):
    attrs = {
        'id': 1,
        'email': 'admin@soseki.io',
        'name': 'Soseki Admin',
        'roles': [SSK_ADMIN_GROUP]
    }
    my_app_settings = AppSettings()

    current_user.return_value = mock.Mock(is_authenticated=True,
                                          is_anonymous=False, **attrs)
    current_user.return_value.is_admin.return_value = True
    my_tst_email = current_app.config["USER_FREE_EMAIL"]
    my_cmd = ConfigCmd()

    my_test_str_key = "teststrkey"
    my_test_str_val = "testval"
    my_params = ["s", my_tst_email, SettingParser.STR_TYPE, my_test_str_key, my_test_str_val]
    my_ok, my_res = my_cmd.exec(my_params)
    assert my_ok
    my_setting = my_app_settings.get_setting(my_test_str_key, my_tst_email)
    assert my_setting == my_test_str_val

    my_params = ["d", my_tst_email, my_test_str_key]
    my_ok, my_res = my_cmd.exec(my_params)
    assert my_ok

    my_setting = my_app_settings.get_setting(my_test_str_key, my_tst_email)
    assert my_setting is None


@mock.patch('flask_login.utils._get_user')
def run_glb_conf(current_user):
    attrs = {
        'id': 1,
        'email': 'admin@soseki.io',
        'name': 'Soseki Admin',
        'roles': [SSK_ADMIN_GROUP]
    }
    my_app_settings = AppSettings()

    current_user.return_value = mock.Mock(is_authenticated=True,
                                          is_anonymous=False, **attrs)
    current_user.return_value.is_admin.return_value = True
    my_tst_email = current_app.config["USER_FREE_EMAIL"]
    my_cmd = ConfigCmd()

    my_test_str_key = "teststrkey"
    my_test_str_val = "testval"
    my_params = ["s", my_tst_email, SettingParser.STR_TYPE, my_test_str_key, my_test_str_val]
    my_ok, my_res = my_cmd.exec(my_params)
    assert my_ok
    my_setting = my_app_settings.get_setting(my_test_str_key, my_tst_email)
    assert my_setting == my_test_str_val

    #as non admin
    my_params = ["gl", my_test_str_key, "on"]
    my_ok, my_res = my_cmd.exec(my_params)
    assert not my_ok

    my_tst_email = current_app.config["ADMIN_EMAIL"]
    my_test_str_key = "teststr_global_key"
    my_test_str_val = "testval"
    my_params = ["s", my_tst_email, SettingParser.STR_TYPE, my_test_str_key, my_test_str_val]
    my_ok, my_res = my_cmd.exec(my_params)
    assert my_ok

    #admin
    my_params = ["gl", my_test_str_key, "on"]
    my_ok, my_res = my_cmd.exec(my_params)
    assert my_ok

    assert my_app_settings.is_global(my_test_str_key)

    from ssk.models.setting import Setting
    my_tst_setting = Setting.get_by_key(my_test_str_key)
    assert my_tst_setting.system

    #ToDo
    # my_tst_setting = Setting.get_global_by_key(my_test_str_key)
    # assert my_tst_setting is not None

    #admin
    my_params = ["gl", my_test_str_key, "off"]
    my_ok, my_res = my_cmd.exec(my_params)
    assert my_ok

    my_nok, my_mesg = my_app_settings.is_global(my_test_str_key)
    assert not my_nok

    from ssk.models.setting import Setting
    my_tst_setting = Setting.get_by_key(my_test_str_key)
    assert not my_tst_setting.system


def test_smoke(app):
    with app.app_context():

        run_ls_conf()

@mock.patch('flask_login.utils._get_user')
def run_consts(current_user):
    attrs = {
        'id': 1,
        'email': 'admin@soseki.io',
        'name': 'Soseki Admin',
        'roles': [SSK_ADMIN_GROUP]
    }
    current_user.return_value = mock.Mock(is_authenticated=True,
                                          is_anonymous=False, **attrs)
    current_user.return_value.is_admin.return_value = True

    my_cmd = ConfigCmd()
    my_params = ["c"]
    my_ok, my_res = my_cmd.exec(my_params)
    assert my_ok


def test_contst(app):
    with app.app_context():
        run_consts()


def test_setget(app):
    with app.app_context():

        run_setget_conf()


def test_del(app):
    with app.app_context():

        run_del_conf()


def test_global(app):
    with app.app_context():

        run_glb_conf()
