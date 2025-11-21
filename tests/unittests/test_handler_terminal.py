#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#

from unittest.mock import patch

from ssk.blueprints.cmd_handler import CmdHandler
from ssk.ssk_consts import SSK_ADMIN_GROUP
from unittest import mock


def test_terminal(app):
    with app.app_context():
        with patch('flask_login.utils._get_user') as current_user_mock:
            current_user_mock.return_value = mock.Mock(is_authenticated=True,
                                                       is_anonymous=False,
                                                       id=1,
                                                       roles=[SSK_ADMIN_GROUP])
            current_user_mock.return_value.is_admin.return_value = True

            my_handler = CmdHandler()
            my_file = my_handler.get_terminal()

            assert my_file == CmdHandler.PAGE_TERMINAL

