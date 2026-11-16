#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#

from flask import current_app
from flask_login import UserMixin as FlaskLoginUserMixin


class UserMixin(FlaskLoginUserMixin):
    """Flask-Login user with roles. Expects `id`, `password`, `active` and `roles` attributes."""

    def get_id(self):
        # '<id>|<password fingerprint>': see UserManager.load_user
        return '{}|{}'.format(self.id, current_app.user_manager.password_fingerprint(self))

    @property
    def is_active(self):
        return bool(getattr(self, 'active', True))

    def has_roles(self, *requirements):
        """True if the user has every listed role. A list or tuple means "any one of these".

        has_roles('a', 'b')          -> a AND b
        has_roles(('a', 'b'), 'c')   -> (a OR b) AND c
        """
        my_role_names = {my_role.name for my_role in getattr(self, 'roles', [])}
        for my_requirement in requirements:
            if isinstance(my_requirement, (list, tuple)):
                if not my_role_names.intersection(my_requirement):
                    return False
            elif my_requirement not in my_role_names:
                return False
        return True
