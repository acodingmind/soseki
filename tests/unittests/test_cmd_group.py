#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#
from flask import current_app

from ssk import SSK_ADMIN_GROUP
from ssk.logic.cmd.group_cmd import GroupCmd

from unittest import mock


@mock.patch('flask_login.utils._get_user')
def run_admin_group(current_user):
    attrs = {
        'id': 1,
        'email': 'admin@soseki.io',
        'name': 'Soseki Admin',
        'roles': [SSK_ADMIN_GROUP]
    }
    current_user.return_value = mock.Mock(is_authenticated=True,
                                          is_anonymous=False, **attrs)
    current_user.return_value.is_admin.return_value = True

    my_cmd = GroupCmd()
    my_params = ["l"]
    my_res, my_mesg = my_cmd.action(my_params)
    assert my_res

    my_user_group = current_app.config["USER_GROUP_NAME"]
    my_admin_group = current_app.config["ADMIN_GROUP_NAME"]
    my_tst_email = current_app.config["USER_FREE_EMAIL"]

    from ssk.models.user import User
    my_tst_user = User.get_by_email(my_tst_email)
    assert my_tst_user.active

    assert my_tst_user.has_role(my_user_group)
    assert not my_tst_user.has_role(my_admin_group)

    my_params = ["a", my_tst_email, my_admin_group]
    my_res, my_mesg = my_cmd.action(my_params)
    assert my_res

    my_tst_user = User.get_by_email(my_tst_email)
    assert my_tst_user.has_role(my_user_group)
    assert my_tst_user.has_role(my_admin_group)

    my_params = ["d", my_tst_email, my_admin_group]
    my_res, my_mesg = my_cmd.action(my_params)
    assert my_res

    my_tst_user = User.get_by_email(my_tst_email)
    assert my_tst_user.has_role(my_user_group)
    assert not my_tst_user.has_role(my_admin_group)


@mock.patch('flask_login.utils._get_user')
def run_new_group(current_user):
    attrs = {
        'id': 1,
        'email': 'admin@soseki.io',
        'name': 'Soseki Admin',
        'roles': [SSK_ADMIN_GROUP]
    }
    current_user.return_value = mock.Mock(is_authenticated=True,
                                          is_anonymous=False, **attrs)
    current_user.return_value.is_admin.return_value = True

    my_cmd = GroupCmd()
    my_params = ["l"]
    my_res, my_mesg = my_cmd.action(my_params)
    assert my_res

    my_test_group = "test_group"
    my_params = ["n", my_test_group]
    my_res, my_mesg = my_cmd.action(my_params)
    assert my_res

    my_tst_email = current_app.config["USER_FREE_EMAIL"]

    from ssk.models.user import User
    my_tst_user = User.get_by_email(my_tst_email)
    assert my_tst_user.active

    assert not my_tst_user.has_role(my_test_group)

    my_params = ["a", my_tst_email, my_test_group]
    my_res, my_mesg = my_cmd.action(my_params)
    assert my_res

    my_tst_user = User.get_by_email(my_tst_email)
    assert my_tst_user.has_role(my_test_group)

    my_params = ["d", my_tst_email, my_test_group]
    my_res, my_mesg = my_cmd.action(my_params)
    assert my_res

    my_tst_user = User.get_by_email(my_tst_email)
    assert not my_tst_user.has_role(my_test_group)

def test_admin_group(app):
    with app.app_context():
        run_admin_group()

def test_new_group(app):
    with app.app_context():
        run_new_group()
