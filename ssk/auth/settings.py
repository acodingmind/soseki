#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#

# Defaults for the USER_* settings. The names and defaults match Flask-User 1.0, which this
# module replaces, so existing app configs and templates keep working. Any of them can be
# overridden in the app's YAML config.
DEFAULTS = {
    # features
    "USER_ENABLE_EMAIL": True,
    "USER_ENABLE_USERNAME": True,
    "USER_ENABLE_CHANGE_USERNAME": True,
    "USER_ENABLE_CHANGE_PASSWORD": True,
    "USER_ENABLE_CONFIRM_EMAIL": True,
    "USER_ENABLE_FORGOT_PASSWORD": True,
    "USER_ENABLE_INVITE_USER": False,
    "USER_ENABLE_REGISTER": True,
    "USER_ENABLE_REMEMBER_ME": True,
    "USER_REQUIRE_INVITATION": False,
    "USER_REQUIRE_RETYPE_PASSWORD": True,
    "USER_ALLOW_LOGIN_WITHOUT_CONFIRMED_EMAIL": False,
    "USER_SHOW_EMAIL_DOES_NOT_EXIST": False,
    "USER_SHOW_USERNAME_DOES_NOT_EXIST": False,

    # always off; kept so templates written for Flask-User don't break
    "USER_ENABLE_AUTH0": False,
    "USER_ENABLE_MULTIPLE_EMAILS": False,

    # app info
    "USER_APP_NAME": "USER_APP_NAME",
    "USER_APP_VERSION": "v1.0",

    # behaviour
    "USER_AUTO_LOGIN_AFTER_CONFIRM": True,
    "USER_AUTO_LOGIN_AFTER_REGISTER": True,
    "USER_AUTO_LOGIN_AFTER_RESET_PASSWORD": True,
    "USER_AUTO_LOGIN_AT_LOGIN": True,
    "USER_SEND_PASSWORD_CHANGED_EMAIL": True,
    "USER_SEND_REGISTERED_EMAIL": True,
    "USER_SEND_USERNAME_CHANGED_EMAIL": True,
    "USER_EMAIL_SENDER_EMAIL": "",
    "USER_EMAIL_SENDER_NAME": "",
    "USER_BCRYPT_ROUNDS": 12,

    # token and session lifetimes, in seconds
    "USER_CONFIRM_EMAIL_EXPIRATION": 2 * 24 * 3600,
    "USER_INVITE_EXPIRATION": 90 * 24 * 3600,
    "USER_RESET_PASSWORD_EXPIRATION": 2 * 24 * 3600,
    "USER_USER_SESSION_EXPIRATION": 3600,

    # URLs
    "USER_CHANGE_PASSWORD_URL": "/user/change-password",
    "USER_CHANGE_USERNAME_URL": "/user/change-username",
    "USER_CONFIRM_EMAIL_URL": "/user/confirm-email/<token>",
    "USER_EDIT_USER_PROFILE_URL": "/user/edit_user_profile",
    "USER_FORGOT_PASSWORD_URL": "/user/forgot-password",
    "USER_INVITE_USER_URL": "/user/invite",
    "USER_LOGIN_URL": "/user/sign-in",
    "USER_LOGOUT_URL": "/user/sign-out",
    "USER_REGISTER_URL": "/user/register",
    "USER_RESEND_EMAIL_CONFIRMATION_URL": "/user/resend-email-confirmation",
    "USER_RESET_PASSWORD_URL": "/user/reset-password/<token>",

    # page templates
    "USER_CHANGE_PASSWORD_TEMPLATE": "flask_user/change_password.html",
    "USER_CHANGE_USERNAME_TEMPLATE": "flask_user/change_username.html",
    "USER_EDIT_USER_PROFILE_TEMPLATE": "flask_user/edit_user_profile.html",
    "USER_FORGOT_PASSWORD_TEMPLATE": "flask_user/forgot_password.html",
    "USER_INVITE_USER_TEMPLATE": "flask_user/invite_user.html",
    "USER_LOGIN_TEMPLATE": "flask_user/login.html",
    "USER_REGISTER_TEMPLATE": "flask_user/register.html",
    "USER_RESEND_CONFIRM_EMAIL_TEMPLATE": "flask_user/resend_confirm_email.html",
    "USER_RESET_PASSWORD_TEMPLATE": "flask_user/reset_password.html",

    # email templates (prefix; '_subject.txt', '_message.html' and '_message.txt' are appended)
    "USER_CONFIRM_EMAIL_TEMPLATE": "flask_user/emails/confirm_email",
    "USER_INVITE_USER_EMAIL_TEMPLATE": "flask_user/emails/invite_user",
    "USER_PASSWORD_CHANGED_EMAIL_TEMPLATE": "flask_user/emails/password_changed",
    "USER_REGISTERED_EMAIL_TEMPLATE": "flask_user/emails/registered",
    "USER_RESET_PASSWORD_EMAIL_TEMPLATE": "flask_user/emails/reset_password",
    "USER_USERNAME_CHANGED_EMAIL_TEMPLATE": "flask_user/emails/username_changed",

    # where to go after each action ('' means '/')
    "USER_AFTER_CHANGE_PASSWORD_ENDPOINT": "",
    "USER_AFTER_CHANGE_USERNAME_ENDPOINT": "",
    "USER_AFTER_CONFIRM_ENDPOINT": "",
    "USER_AFTER_EDIT_USER_PROFILE_ENDPOINT": "",
    "USER_AFTER_FORGOT_PASSWORD_ENDPOINT": "",
    "USER_AFTER_LOGIN_ENDPOINT": "",
    "USER_AFTER_LOGOUT_ENDPOINT": "",
    "USER_AFTER_REGISTER_ENDPOINT": "",
    "USER_AFTER_RESEND_EMAIL_CONFIRMATION_ENDPOINT": "",
    "USER_AFTER_RESET_PASSWORD_ENDPOINT": "",
    "USER_AFTER_INVITE_ENDPOINT": "",
    "USER_UNAUTHENTICATED_ENDPOINT": "user.login",
    "USER_UNAUTHORIZED_ENDPOINT": "",
}
