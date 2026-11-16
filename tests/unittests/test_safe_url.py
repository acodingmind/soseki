#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#

from urllib.parse import urlsplit

import pytest
from flask import current_app

import ssk  # noqa: F401  (applies the Flask-User patches)
from flask_user import UserManager


def _make_safe_url(a_url):
    return UserManager.make_safe_url(UserManager.__new__(UserManager), a_url)


def _is_local(a_url):
    # browsers treat '\' as '/', so check both forms
    for my_form in (a_url, a_url.replace('\\', '/')):
        my_parts = urlsplit(my_form)
        if my_parts.scheme or my_parts.netloc or my_form.startswith('//'):
            return False
    return True


@pytest.mark.parametrize("a_url", [
    "https://evil.com/path",
    "//evil.com/path",
    "/////evil.com/path",
    "\\\\\\evil.com/path",
    "/\\evil.com/path",
    "\\/evil.com/path",
    "/\t/evil.com/path",
    "/\n/evil.com/path",
    " //evil.com/path",
    "\x00//evil.com/path",
])
def test_make_safe_url_blocks_open_redirect(a_url):
    # CVE-2021-23401
    assert _is_local(_make_safe_url(a_url))


@pytest.mark.parametrize("a_url, a_expected", [
    ("/ssk/tasks", "/ssk/tasks"),
    ("/ssk/tasks?a=1#frag", "/ssk/tasks?a=1#frag"),
    ("https://myhost:8080/ssk/tasks?a=1", "/ssk/tasks?a=1"),
    ("", ""),
    (None, ""),
])
def test_make_safe_url_keeps_local_urls(a_url, a_expected):
    assert _make_safe_url(a_url) == a_expected


def test_login_next_cannot_redirect_off_site(app, client):
    with app.app_context():
        my_username = current_app.config["USER_FREE_NAME"]
        my_password = current_app.config["USER_FREE_PASS"]

    my_response = client.post("/user/sign-in",
                              data={"username": my_username, "password": my_password, "next": "/////evil.com/path"})

    assert my_response.status_code == 302
    my_location = my_response.headers["Location"]
    assert _is_local(my_location), my_location
