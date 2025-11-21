#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#
from unittest.mock import patch
from ssk import get_db
from ssk.blueprints.home_handler import HomeHandler
from ssk.ssk_consts import SSK_ADMIN_GROUP
from unittest import mock

from ssk.globals.contacts_mgr import ContactMgr


FLASK_LOGINXUTILSX_GETUSER = 'flask_login.utils._get_user'



def test_tasks(app):
    with app.app_context():
        with patch(FLASK_LOGINXUTILSX_GETUSER) as current_user_mock:
            current_user_mock.return_value = mock.Mock(is_authenticated=True,
                                                       is_anonymous=False,
                                                       id=1,
                                                       roles=[SSK_ADMIN_GROUP])
            current_user_mock.return_value.is_admin.return_value = True
            my_file, my_tasks = HomeHandler.tasks()

            assert my_file == HomeHandler.PAGE_TASKS
            assert len(my_tasks) == 0


def test_tasks_action(app):
    with app.app_context():
        with patch(FLASK_LOGINXUTILSX_GETUSER) as current_user_mock:
            current_user_mock.return_value = mock.Mock(is_authenticated=True,
                                                       is_anonymous=False,
                                                       id=1,
                                                       roles=[SSK_ADMIN_GROUP])
            current_user_mock.return_value.is_admin.return_value = True
            my_request_mock = mock.Mock()
            my_request_mock.method = "POST"
            my_request_mock.headers = {'content-type': 'application/json'}
            my_request_mock.form = {'stop': -1, 'delete': -1}

            my_file, my_tasks = HomeHandler.tasks_action(my_request_mock)

            assert my_file == HomeHandler.PAGE_TASKS
            assert len(my_tasks) == 0


def test_contact_post(app):
    with app.app_context():
        with patch(FLASK_LOGINXUTILSX_GETUSER) as current_user_mock:
            current_user_mock.return_value = mock.Mock(is_authenticated=True,
                                                       is_anonymous=False,
                                                       roles=[SSK_ADMIN_GROUP])
            current_user_mock.return_value.is_admin.return_value = True

            my_request_mock = mock.Mock()
            my_request_mock.method = "POST"
            my_request_mock.headers = {'content-type': 'application/json'}

            my_request_mock.form = {"source": "about",
                                    'name': "some name",
                                    "email": "some@email.com",
                                    "message": "test message"}

            my_db_session = get_db().session
            my_contact_mgr = ContactMgr(my_db_session)
            assert len(my_contact_mgr.get_all_keys()) == 0

            my_file, my_contact_form, my_messgae = HomeHandler.post_contact(my_request_mock)

            assert my_file == HomeHandler.PAGE_ABOUT
            assert len(my_contact_mgr.get_all_keys()) == 1
