#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#

"""Soseki's user accounts: sign-in, registration, email confirmation, password reset and roles.

Built on Flask-Login, bcrypt and itsdangerous. It replaces Flask-User (unmaintained since 2019)
and passlib, keeping their USER_* settings, /user/... URLs, user.* endpoint names and templates.
"""

from flask_login import current_user

from .decorators import login_required, roles_accepted, roles_required
from .manager import ConfigError, UserManager, truncate_password
from .mixins import UserMixin

__all__ = ['UserManager', 'UserMixin', 'ConfigError', 'current_user', 'login_required',
           'roles_accepted', 'roles_required', 'truncate_password']
