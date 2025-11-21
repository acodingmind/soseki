#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#
from unittest.mock import patch
from ssk.blueprints.cmd_handler import CmdHandler
from ssk.ssk_consts import SSK_ADMIN_GROUP
from unittest import mock
import json


def test_terminal(app):
    with app.app_context():
        with patch('flask_login.utils._get_user') as current_user_mock:
            current_user_mock.return_value = mock.Mock(is_authenticated=True,
                                                       is_anonymous=False,
                                                       roles=[SSK_ADMIN_GROUP])
            current_user_mock.return_value.is_admin.return_value = True

            my_file = CmdHandler.get_terminal()

            assert my_file == CmdHandler.PAGE_TERMINAL


def test_post_cmd(app):
    with app.app_context():
        with patch('flask_login.utils._get_user') as current_user_mock:
            current_user_mock.return_value = mock.Mock(is_authenticated=True,
                                                       is_anonymous=False,
                                                       roles=[SSK_ADMIN_GROUP])
            current_user_mock.return_value.is_admin.return_value = True

            my_request_mock = mock.Mock()
            my_request_mock.method = "POST"
            my_request_mock.headers = {'content-type': 'application/json'}
            my_request_mock.json = {'method': '?', "params": []}

            my_json = CmdHandler.cmd_post(my_request_mock)
            my_json_dict = json.loads(my_json)
            assert my_json_dict['id'] == 3
