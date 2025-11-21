#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#
from unittest.mock import patch
from flask import current_app
from ssk.blueprints.api_handler import ApiHandler
from ssk.ssk_consts import SSK_ADMIN_GROUP
from unittest import mock

from ssk.globals.api_gate import ApiGate

APPLICATION_JSON = 'application/json'
FLASK_LOGINXUTILSX_GET_USER = 'flask_login.utils._get_user'


def test_access(app):
    with app.app_context():
        with patch(FLASK_LOGINXUTILSX_GET_USER) as current_user_mock:
            current_user_mock.return_value = mock.Mock(is_authenticated=True,
                                                       is_anonymous=False,
                                                       roles=[SSK_ADMIN_GROUP])
            current_user_mock.return_value.is_admin.return_value = True

            my_request_mock = mock.Mock()
            my_request_mock.method = "POST"
            my_request_mock.headers = {'content-type': APPLICATION_JSON}
            my_request_mock.json = {"echo": ""}

            my_api_gate = ApiGate()
            my_api_gate.init()
            my_api_gate.load()
            my_api_gate.set_open(True)

            my_data, my_ret_val = ApiHandler.echo(my_request_mock, "1", "wrong_key")
            assert my_ret_val == 400

            my_data, my_ret_val = ApiHandler.status("1", "wrong_key")
            assert my_ret_val == 400

            my_zero_user = current_app.config["USER_FREE_EMAIL"]
            my_new_key = my_api_gate.add_api_key(my_zero_user)
            assert my_new_key is not None

            my_data, my_ret_val = ApiHandler.echo(my_request_mock, "1", my_new_key)
            assert my_ret_val == 200

            my_data, my_ret_val = ApiHandler.status("1", my_new_key)
            assert my_ret_val == 200


def test_echo(app):
    with app.app_context():
        with patch(FLASK_LOGINXUTILSX_GET_USER) as current_user_mock:
            current_user_mock.return_value = mock.Mock(is_authenticated=True,
                                                       is_anonymous=False,
                                                       roles=[SSK_ADMIN_GROUP])
            current_user_mock.return_value.is_admin.return_value = True

            my_echo_test_mesg = "some test mesg"

            my_request_mock = mock.Mock()
            my_request_mock.method = "POST"
            my_request_mock.headers = {'content-type': APPLICATION_JSON}
            my_request_mock.json = {"echo": my_echo_test_mesg}

            my_api_gate = ApiGate()
            my_api_gate.init()
            my_api_gate.load()
            my_api_gate.set_open(True)

            my_zero_user = current_app.config["USER_FREE_EMAIL"]
            my_new_key = my_api_gate.add_api_key(my_zero_user)
            assert my_new_key is not None

            my_data, my_ret_val = ApiHandler.echo(my_request_mock, "1", my_new_key)
            assert my_ret_val == 200
            assert my_data == my_echo_test_mesg

def test_status(app):
    with app.app_context():
        with patch(FLASK_LOGINXUTILSX_GET_USER) as current_user_mock:
            current_user_mock.return_value = mock.Mock(is_authenticated=True,
                                                       is_anonymous=False,
                                                       roles=[SSK_ADMIN_GROUP])
            current_user_mock.return_value.is_admin.return_value = True

            my_api_gate = ApiGate()
            my_api_gate.init()
            my_api_gate.load()
            my_api_gate.set_open(True)

            my_zero_user = current_app.config["USER_FREE_EMAIL"]
            my_new_key = my_api_gate.add_api_key(my_zero_user)
            assert my_new_key is not None

            my_data, my_ret_val = ApiHandler.status("1", my_new_key)
            assert my_ret_val == 200

