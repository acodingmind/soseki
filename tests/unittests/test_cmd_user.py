#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#

from flask import current_app

from ssk import SSK_ADMIN_GROUP
from ssk.logic.cmd.user_cmd import UserCmd
from ssk.logic.cmd.change_pass_cmd import ChangePasswdCmd
from ssk.logic.cmd.validate_cmd import ValidateUserCmd


from unittest import mock


@mock.patch('flask_login.utils._get_user')
def run_enable_disable(current_user):
    attrs = {
        'id': 1,
        'email': 'admin@soseki.io',
        'name': 'Soseki Admin',
        'roles': [SSK_ADMIN_GROUP]
    }
    current_user.return_value = mock.Mock(is_authenticated=True,
                                          is_anonymous=False, **attrs)
    current_user.return_value.is_admin.return_value = True

    my_cmd = UserCmd()
    my_params = ["l"]
    my_ok, my_res = my_cmd.exec(my_params)
    assert my_ok

    my_tst_email = current_app.config["USER_FREE_EMAIL"]

    from ssk.models.user import User
    my_tst_user = User.get_by_email(my_tst_email)
    assert my_tst_user.active

    #disable
    my_params = ["disable", my_tst_email]
    my_res, my_mesg = my_cmd.action(my_params)
    assert my_res

    my_tst_user = User.get_by_email(my_tst_email)
    assert not my_tst_user.active

    my_params = ["enable", my_tst_email]
    my_res, my_mesg = my_cmd.action(my_params)
    assert my_res

    my_tst_user = User.get_by_email(my_tst_email)
    assert my_tst_user.active


@mock.patch('flask_login.utils._get_user')
def run_delete(current_user):
    attrs = {
        'id': 1,
        'email': 'admin@soseki.io',
        'name': 'Soseki Admin',
        'roles': [SSK_ADMIN_GROUP]
    }
    current_user.return_value = mock.Mock(is_authenticated=True,
                                          is_anonymous=False, **attrs)
    current_user.return_value.is_admin.return_value = True

    my_cmd = UserCmd()
    my_params = ["l"]
    my_ok, my_res = my_cmd.exec(my_params)
    assert my_ok

    my_tst_email = current_app.config["USER_FREE_EMAIL"]

    from ssk.models.user import User
    my_tst_user = User.get_by_email(my_tst_email)
    assert my_tst_user.active

    # cannot remove active user
    my_params = ["remove", my_tst_email]
    my_ok, my_res = my_cmd.exec(my_params)
    assert not my_ok

    #disable
    my_params = ["disable", my_tst_email]
    my_res, my_mesg = my_cmd.action(my_params)
    assert my_res

    # cannot remove active user
    my_params = ["remove", my_tst_email]
    my_ok, my_res = my_cmd.exec(my_params)
    assert my_ok


@mock.patch('flask_login.utils._get_user')
def run_chpass(current_user):
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
    my_tst_pass = current_app.config["USER_FREE_PASS"]
    my_new_pass = "SomeNewPa@SS1"
    my_wrong_pass = "SomeWrongPass"

    my_cmd = ValidateUserCmd()
    my_params = [my_tst_email, my_wrong_pass]
    my_res, my_mesg = my_cmd.action(my_params)
    assert not my_res

    my_cmd = ValidateUserCmd()
    my_params = [my_tst_email, my_tst_pass]
    my_res, my_mesg = my_cmd.action(my_params)
    assert my_res

    my_cmd = ChangePasswdCmd()
    my_params = [my_tst_email, my_new_pass]
    my_res, my_mesg = my_cmd.action(my_params)
    assert my_res

    my_cmd = ValidateUserCmd()
    my_params = [my_tst_email, my_new_pass]
    my_res, my_mesg = my_cmd.action(my_params)
    assert my_res


def test_user_enable_disable(app):
    with app.app_context():
        run_enable_disable()


def test_user_delete(app):
    with app.app_context():
        run_delete()


def test_user_chpass(app):
    with app.app_context():
        run_chpass()

