#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#
from flask import current_app

from ssk.globals.api_gate import ApiGate

from ssk import SSK_ADMIN_GROUP
from ssk.logic.cmd.api_cmd import ApiCmd

from unittest import mock


@mock.patch('flask_login.utils._get_user')
def run_ls_apikey(current_user):
    attrs = {
        'id': 1,
        'email': 'admin@soseki.io',
        'name': 'Soseki Admin',
        'roles': [SSK_ADMIN_GROUP]
    }
    current_user.return_value = mock.Mock(is_authenticated=True,
                                          is_anonymous=False, **attrs)
    current_user.return_value.is_admin.return_value = True

    my_cmd = ApiCmd()
    my_params = ["l"]
    my_ok, my_res = my_cmd.exec(my_params)
    assert my_ok


@mock.patch('flask_login.utils._get_user')
def run_add_apikey(current_user):
    attrs = {
        'id': 1,
        'email': 'admin@soseki.io',
        'name': 'Soseki Admin',
        'roles': [SSK_ADMIN_GROUP]
    }
    current_user.return_value = mock.Mock(is_authenticated=True,
                                          is_anonymous=False, **attrs)
    current_user.return_value.is_admin.return_value = True

    my_tst_email = current_app.config["USER_FREE_EMAIL"]

    my_cmd = ApiCmd()
    my_params = ["add", my_tst_email]
    my_ok, my_res = my_cmd.exec(my_params)
    assert my_ok


@mock.patch('flask_login.utils._get_user')
def run_on_apikey(current_user):
    attrs = {
        'id': 1,
        'email': 'admin@soseki.io',
        'name': 'Soseki Admin',
        'roles': [SSK_ADMIN_GROUP]
    }
    current_user.return_value = mock.Mock(is_authenticated=True,
                                          is_anonymous=False, **attrs)
    current_user.return_value.is_admin.return_value = True

    my_tst_email = current_app.config["USER_FREE_EMAIL"]
    from ssk.models.user import User
    my_tst_user = User.get_by_email(my_tst_email)
    from ssk.models.apikey import ApiKey
    my_user_key = ApiKey.get_by_user(my_tst_user.id)

    my_cmd = ApiCmd()
    my_params = ["enable", my_user_key[0].key]
    my_ok, my_res = my_cmd.exec(my_params)
    assert my_ok


@mock.patch('flask_login.utils._get_user')
def run_off_apikey(current_user):
    attrs = {
        'id': 1,
        'email': 'admin@soseki.io',
        'name': 'Soseki Admin',
        'roles': [SSK_ADMIN_GROUP]
    }
    current_user.return_value = mock.Mock(is_authenticated=True,
                                          is_anonymous=False, **attrs)
    current_user.return_value.is_admin.return_value = True

    my_tst_email = current_app.config["USER_FREE_EMAIL"]
    from ssk.models.user import User
    my_tst_user = User.get_by_email(my_tst_email)
    from ssk.models.apikey import ApiKey
    my_user_key = ApiKey.get_by_user(my_tst_user.id)

    my_cmd = ApiCmd()
    my_params = ["disable", my_user_key[0].key]
    my_ok, my_res = my_cmd.exec(my_params)
    assert my_ok


def test_api_access(app):
    with app.app_context():
        my_api_gate = ApiGate()
        my_api_gate.init()
        my_api_gate.load()

        my_tst_email = current_app.config["USER_FREE_EMAIL"]

        from ssk.models.user import User
        my_tst_user = User.get_by_email(my_tst_email)

        from ssk.models.apikey import ApiKey
        my_user_key = ApiKey.get_by_user(my_tst_user.id)

        my_num_of_keys = len(my_user_key)
        assert my_num_of_keys == 0

        run_ls_apikey()
        run_add_apikey()

        my_user_key = ApiKey.get_by_user(my_tst_user.id)

        my_num_of_keys = len(my_user_key)
        assert my_num_of_keys == 1

        my_api_key = my_user_key[0].key

        # first closed ApiGate
        assert not my_api_gate.is_valid(current_app, my_api_key)

        my_api_gate.set_open(True)
        # now open
        assert my_api_gate.is_valid(current_app, my_api_key)

        run_off_apikey()
        assert not my_api_gate.is_valid(current_app, my_api_key)

        run_on_apikey()
        assert my_api_gate.is_valid(current_app, my_api_key)
        assert my_api_gate.is_active_now(my_api_key)
        assert my_api_gate.num_active_keys() == 1

        run_add_apikey()
        my_user_key = ApiKey.get_by_user(my_tst_user.id)
        assert my_api_gate.num_active_keys() == 1
        assert not my_api_gate.is_active_now(my_user_key[1].key)

        assert my_api_gate.is_valid(current_app, my_user_key[1].key)
        assert my_api_gate.num_active_keys() == 2
        assert my_api_gate.is_active_now(my_user_key[1].key)

