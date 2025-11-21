#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#
from ssk import get_db, SSK_ADMIN_GROUP
from ssk.globals.contacts_mgr import ContactMgr
from unittest import mock


def test_contact_cnt(app):
    with app.app_context():
        my_db_session = get_db().session
        my_contact_mgr = ContactMgr(my_db_session)

        assert len(my_contact_mgr.get_all_keys()) == 0


@mock.patch('flask_login.utils._get_user')
def run_add_contact(current_user):
    attrs = {
        'id': 1,
        'email': 'admin@soseki.io',
        'name': 'Soseki Admin',
        'roles': [SSK_ADMIN_GROUP]
    }
    current_user.return_value = mock.Mock(is_authenticated=True,
                                          is_anonymous=False, **attrs)
    current_user.return_value.is_admin.return_value = True

    my_db_session = get_db().session
    my_contact_mgr = ContactMgr(my_db_session)

    my_ret_val, my_message = my_contact_mgr.add_post("name", "mail", "message", "source")
    assert my_ret_val
    if my_ret_val:
        my_contact_mgr.commit()

    assert len(my_contact_mgr.get_all_keys()) == 1

    # check if duplicates are not added
    my_ret_val, my_message = my_contact_mgr.add_post("name", "mail", "message", "source")
    assert not my_ret_val
    assert len(my_contact_mgr.get_all_keys()) == 1


def test_contact_add(app):
    with app.app_context():
        run_add_contact()
