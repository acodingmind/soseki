#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#

from functools import wraps
from urllib.parse import quote

from flask import current_app, flash, redirect, request, url_for
from flask_login import current_user


def _endpoint_url(an_endpoint):
    return url_for(an_endpoint) if an_endpoint else '/'


def unauthenticated_view():
    """Send the visitor to the sign-in page, coming back here afterwards."""
    my_user_manager = current_app.user_manager
    flash("You must be signed in to access '{}'.".format(request.path), 'error')
    my_next = my_user_manager.make_safe_url(request.full_path if request.query_string else request.path)
    return redirect(_endpoint_url(my_user_manager.USER_UNAUTHENTICATED_ENDPOINT) + '?next=' + quote(my_next))


def unauthorized_view():
    flash("You do not have permission to access '{}'.".format(request.script_root + request.path), 'error')
    return redirect(_endpoint_url(current_app.user_manager.USER_UNAUTHORIZED_ENDPOINT))


def is_signed_in_with_confirmed_email():
    if not current_user or not current_user.is_authenticated:
        return False
    my_user_manager = current_app.user_manager
    if my_user_manager.USER_ENABLE_CONFIRM_EMAIL and not my_user_manager.USER_ALLOW_LOGIN_WITHOUT_CONFIRMED_EMAIL:
        return bool(getattr(current_user, 'email_confirmed_at', None))
    return True


def login_required(a_view):
    @wraps(a_view)
    def decorator(*args, **kwargs):
        if not is_signed_in_with_confirmed_email():
            return unauthenticated_view()
        return a_view(*args, **kwargs)
    return decorator


def roles_required(*role_names):
    """The user needs every role. A list or tuple stands for "any one of these"."""
    def wrapper(a_view):
        @wraps(a_view)
        def decorator(*args, **kwargs):
            if not is_signed_in_with_confirmed_email():
                return unauthenticated_view()
            if not current_user.has_roles(*role_names):
                return unauthorized_view()
            return a_view(*args, **kwargs)
        return decorator
    return wrapper


def roles_accepted(*role_names):
    """The user needs at least one of the roles."""
    def wrapper(a_view):
        @wraps(a_view)
        def decorator(*args, **kwargs):
            if not is_signed_in_with_confirmed_email():
                return unauthenticated_view()
            if not current_user.has_roles(role_names):
                return unauthorized_view()
            return a_view(*args, **kwargs)
        return decorator
    return wrapper
