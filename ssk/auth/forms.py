#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#

# Field names match Flask-User's forms, so the templates under flask_user/ work unchanged.

from flask import current_app
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import BooleanField, HiddenField, PasswordField, StringField, SubmitField
from wtforms import ValidationError, validators


def password_validator(form, field):
    current_app.user_manager.password_validator(form, field)


def username_validator(form, field):
    current_app.user_manager.username_validator(form, field)


def unique_username_validator(form, field):
    if not current_app.user_manager.username_is_available(field.data):
        raise ValidationError('This Username is already in use. Please try another one.')


def unique_email_validator(form, field):
    if not current_app.user_manager.email_is_available(field.data):
        raise ValidationError('This Email is already in use. Please try another one.')


def _check_current_password(a_field):
    if not current_user or not current_user.is_authenticated or \
            not current_app.user_manager.verify_password(a_field.data, current_user.password):
        a_field.errors.append('Old Password is incorrect')
        return False
    return True


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Old Password', validators=[validators.DataRequired('Old Password is required')])
    new_password = PasswordField('New Password', validators=[
        validators.DataRequired('New Password is required'), password_validator])
    retype_password = PasswordField('Retype New Password', validators=[
        validators.EqualTo('new_password', message='New Password and Retype Password did not match')])
    next = HiddenField()
    submit = SubmitField('Change password')

    def validate(self, extra_validators=None):
        if not current_app.user_manager.USER_REQUIRE_RETYPE_PASSWORD:
            delattr(self, 'retype_password')
        if not super().validate(extra_validators):
            return False
        return _check_current_password(self.old_password)


class ChangeUsernameForm(FlaskForm):
    new_username = StringField('New Username', validators=[
        validators.DataRequired('Username is required'), username_validator, unique_username_validator])
    old_password = PasswordField('Old Password', validators=[validators.DataRequired('Old Password is required')])
    next = HiddenField()
    submit = SubmitField('Change username')

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False
        return _check_current_password(self.old_password)


class EditUserProfileForm(FlaskForm):
    first_name = StringField('First name', validators=[validators.DataRequired()])
    last_name = StringField('Last name', validators=[validators.DataRequired()])
    submit = SubmitField('Update')


class LoginForm(FlaskForm):
    next = HiddenField()
    reg_next = HiddenField()
    username = StringField('Username', validators=[validators.DataRequired('Username is required')])
    email = StringField('Email', validators=[
        validators.DataRequired('Email is required'), validators.Email('Invalid Email')])
    password = PasswordField('Password', validators=[validators.DataRequired('Password is required')])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Sign in')

    # set by validate(): the user whose credentials matched
    user = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        my_user_manager = current_app.user_manager
        if my_user_manager.USER_ENABLE_USERNAME and my_user_manager.USER_ENABLE_EMAIL:
            self.username.label.text = 'Username or Email'

    def validate(self, extra_validators=None):
        my_user_manager = current_app.user_manager
        if my_user_manager.USER_ENABLE_USERNAME:
            delattr(self, 'email')
        else:
            delattr(self, 'username')
        if not super().validate(extra_validators):
            return False

        if my_user_manager.USER_ENABLE_USERNAME:
            my_identity_field = self.username
            my_user = my_user_manager.find_user_by_username(self.username.data)
            if my_user is None and my_user_manager.USER_ENABLE_EMAIL:
                my_user = my_user_manager.find_user_by_email(self.username.data)
        else:
            my_identity_field = self.email
            my_user = my_user_manager.find_user_by_email(self.email.data)

        if my_user is not None and my_user_manager.verify_password(self.password.data, my_user.password):
            self.user = my_user
            return True

        if my_user is None:
            # spend the same time as a real check, so response times don't reveal which accounts exist
            my_user_manager.verify_password(self.password.data, my_user_manager.dummy_password_hash())

        if my_user_manager.USER_ENABLE_USERNAME and my_user_manager.USER_ENABLE_EMAIL:
            my_label = 'Username/Email'
            my_show_missing = my_user_manager.USER_SHOW_EMAIL_DOES_NOT_EXIST or \
                my_user_manager.USER_SHOW_USERNAME_DOES_NOT_EXIST
        elif my_user_manager.USER_ENABLE_USERNAME:
            my_label = 'Username'
            my_show_missing = my_user_manager.USER_SHOW_USERNAME_DOES_NOT_EXIST
        else:
            my_label = 'Email'
            my_show_missing = my_user_manager.USER_SHOW_EMAIL_DOES_NOT_EXIST

        if my_show_missing:
            if my_user is None:
                my_identity_field.errors.append('{} does not exist'.format(my_label))
            else:
                self.password.errors.append('Incorrect Password')
        else:
            my_message = 'Incorrect {} and/or Password'.format(my_label)
            my_identity_field.errors.append(my_message)
            self.password.errors.append(my_message)
        return False


class RegisterForm(FlaskForm):
    next = HiddenField()
    reg_next = HiddenField()
    username = StringField('Username', validators=[
        validators.DataRequired('Username is required'), username_validator, unique_username_validator])
    email = StringField('Email', validators=[
        validators.DataRequired('Email is required'), validators.Email('Invalid Email'), unique_email_validator])
    password = PasswordField('Password', validators=[validators.DataRequired('Password is required'),
                                                     password_validator])
    retype_password = PasswordField('Retype Password', validators=[
        validators.EqualTo('password', message='Password and Retype Password did not match')])
    invite_token = HiddenField('Token')
    submit = SubmitField('Register')

    def validate(self, extra_validators=None):
        my_user_manager = current_app.user_manager
        if not my_user_manager.USER_ENABLE_USERNAME:
            delattr(self, 'username')
        if not my_user_manager.USER_ENABLE_EMAIL:
            delattr(self, 'email')
        if not my_user_manager.USER_REQUIRE_RETYPE_PASSWORD:
            delattr(self, 'retype_password')
        return super().validate(extra_validators)


class ForgotPasswordForm(FlaskForm):
    email = StringField('Your email address', validators=[
        validators.DataRequired('Email address is required'), validators.Email('Invalid Email address')])
    submit = SubmitField('Send reset password email')

    def validate_email(self, field):
        my_user_manager = current_app.user_manager
        if my_user_manager.USER_SHOW_EMAIL_DOES_NOT_EXIST and my_user_manager.find_user_by_email(field.data) is None:
            raise ValidationError('Email does not exist')


class ResendEmailConfirmationForm(FlaskForm):
    email = StringField('Your email address', validators=[
        validators.DataRequired('Email address is required'), validators.Email('Invalid Email address')])
    submit = SubmitField('Resend email confirmation email')


class ResetPasswordForm(FlaskForm):
    new_password = PasswordField('New Password', validators=[
        validators.DataRequired('New Password is required'), password_validator])
    retype_password = PasswordField('Retype New Password', validators=[
        validators.EqualTo('new_password', message='New Password and Retype Password did not match')])
    next = HiddenField()
    submit = SubmitField('Change password')

    def validate(self, extra_validators=None):
        if not current_app.user_manager.USER_REQUIRE_RETYPE_PASSWORD:
            delattr(self, 'retype_password')
        return super().validate(extra_validators)


class InviteUserForm(FlaskForm):
    email = StringField('Email', validators=[validators.DataRequired('Email is required'),
                                             validators.Email('Invalid Email')])
    next = HiddenField()
    submit = SubmitField('Invite!')
