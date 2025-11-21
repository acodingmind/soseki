#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


from flask import current_app
from wtforms import ValidationError


def password_validator(form, field):
    if field.data == "":
        return True

    current_app.user_manager.password_validator(form, field)


def unique_username_validator(form, field):
    my_valid_username = False
    my_new_name = field.data

    my_id = form.id.data

    from ..models.user import User
    my_curr_user = User.get_by_id(my_id)

    if my_curr_user.username == my_new_name:
        my_valid_username = True
    else:
        my_curr_user = User.get_by_name(my_new_name)

        if my_curr_user is None:
            my_valid_username = True

    if not my_valid_username:
        raise ValidationError('This Username is already in use. Please try another one.')


def unique_email_validator(form, field):
    my_valid_email = False
    my_new_email = field.data

    my_id = form.id.data

    from ..models.user import User
    my_curr_user = User.get_by_id(my_id)

    if my_curr_user.email == my_new_email:
        my_valid_email = True
    else:
        my_curr_user = User.get_by_email(my_new_email)

        if my_curr_user is None:
            my_valid_email = True

    if not my_valid_email:
        raise ValidationError('This Email is already in use. Please try another one.')