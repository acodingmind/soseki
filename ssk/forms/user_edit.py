#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


# Flask-WTF v0.13 renamed Flask to FlaskForm
try:
    from flask_wtf import FlaskForm             # Try Flask-WTF v0.13+
except ImportError:
    from flask_wtf import Form as FlaskForm     # Fallback to Flask-WTF v0.12 or older

from wtforms import BooleanField, HiddenField, PasswordField, SubmitField, StringField
from wtforms import validators

from .validators import unique_username_validator, unique_email_validator, password_validator


class EditUserProfileForm(FlaskForm):
    """Edit user profile form."""
    id = HiddenField('id')
    username = StringField('Username', validators=[validators.DataRequired(), unique_username_validator])
    first_name = StringField('First name', validators=[validators.DataRequired()])
    last_name = StringField('Last name', validators=[validators.DataRequired()])
    email = StringField('Email', validators=[validators.DataRequired(), validators.Email('Invalid Email'), unique_email_validator])
    active = BooleanField('Active')

    new_password = PasswordField('New Password', validators=[password_validator,
        ])
    retype_password = PasswordField('Retype New Password', validators=[
        validators.EqualTo('new_password', message='New Password and Retype Password did not match')
        ])

    submit = SubmitField('Save')
