#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#

from unittest.mock import patch

from ssk import SSK_ADMIN_GROUP
from ssk.logic.cmd.anon_cmd import AnonCmd
from ssk.logic.cmd.api_cmd import ApiCmd
from ssk.logic.cmd.job_cmd import JobCmd
from ssk.logic.cmd.change_pass_cmd import ChangePasswdCmd
from ssk.logic.cmd.config_cmd import ConfigCmd
from ssk.logic.cmd.group_cmd import GroupCmd
from ssk.logic.cmd.health_cmd import HealthCmd
from ssk.logic.cmd.mail_cmd import MailCmd
from ssk.logic.cmd.root_cmd import RootCmd
from ssk.logic.cmd.tail_cmd import TailCmd
from ssk.logic.cmd.user_cmd import UserCmd
from ssk.logic.cmd.validate_cmd import ValidateUserCmd

from unittest import mock


def test_anon_access(app):
    with app.app_context():
        with patch('flask_login.utils._get_user') as current_user_mock:
            current_user_mock.return_value = mock.Mock(is_authenticated=False,
                                                       is_anonymous=True)
            current_user_mock.return_value.is_admin.return_value = False

            assert AnonCmd().has_access()

            assert not ApiCmd().has_access()
            assert not ChangePasswdCmd().has_access()
            assert not ConfigCmd().has_access()
            assert not GroupCmd().has_access()
            assert not HealthCmd().has_access()
            assert not JobCmd().has_access()
            assert not MailCmd().has_access()
            assert not RootCmd().has_access()
            assert not TailCmd().has_access()
            assert not UserCmd().has_access()
            assert not ValidateUserCmd().has_access()


def test_user_access(app):
    with app.app_context():
        with patch('flask_login.utils._get_user') as current_user_mock:
            current_user_mock.return_value = mock.Mock(is_authenticated=True,
                                                       is_anonymous=False)
            current_user_mock.return_value.is_admin.return_value = False
            assert AnonCmd().has_access()

            assert not ApiCmd().has_access()
            assert not ChangePasswdCmd().has_access()
            assert not ConfigCmd().has_access()
            assert not GroupCmd().has_access()
            assert not HealthCmd().has_access()
            assert not JobCmd().has_access()
            assert not MailCmd().has_access()
            assert not RootCmd().has_access()
            assert not TailCmd().has_access()
            assert not UserCmd().has_access()
            assert not ValidateUserCmd().has_access()


def test_admin_access(app):
    with app.app_context():
        with patch('flask_login.utils._get_user') as current_user_mock:
            current_user_mock.return_value = mock.Mock(is_authenticated=True,
                                                       is_anonymous=False,
                                                       id=1,
                                                       roles=[SSK_ADMIN_GROUP])
            current_user_mock.return_value.is_admin.return_value = True

            assert AnonCmd().has_access()

            assert ApiCmd().has_access()
            assert ChangePasswdCmd().has_access()
            assert ConfigCmd().has_access()
            assert GroupCmd().has_access()
            assert HealthCmd().has_access()
            assert JobCmd().has_access()
            assert MailCmd().has_access()
            assert RootCmd().has_access()
            assert TailCmd().has_access()
            assert UserCmd().has_access()
            assert ValidateUserCmd().has_access()

