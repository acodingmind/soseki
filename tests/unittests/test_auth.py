#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#

"""End-to-end tests for ssk.auth: real views, templates, database and (captured) emails."""

import re
from contextlib import contextmanager
from urllib.parse import urlsplit

import jinja2
import pytest
from flask import current_app

from ssk.db import get_db
from ssk.models.user import User

# Made by the previous stack (passlib 1.7.4 bcrypt + ssk's 72-byte patch), as stored in existing databases.
LEGACY_HASH_SHORT = "$2b$12$VW.rPazhnJ9B19hNYLV.COTfhvusRkN3Ny8WqoC2Ewa03AyNpgH5O"   # "Legacy-Passw0rd"
LEGACY_HASH_LONG = "$2b$12$0UmE5hyi9.mcGtSk36saueOUdiQNtqdFyH27SYgO8ycR4m531dB/2"    # "Ä" * 40 (80 bytes)
NEW_PASSWORD = "NewPassw0rd"
# the seeded test users have @test.local addresses, which email-validator rejects as reserved
FREE_EMAIL = "free@example.com"


@pytest.fixture()
def auth_app(app):
    # render the real templates (the test app's own template folder is empty)
    app.jinja_loader  # noqa: B018 - make sure Flask built its loader first
    app.jinja_env.loader = jinja2.ChoiceLoader([jinja2.FileSystemLoader("ssk/templates"), app.jinja_env.loader])
    # the layout links to the blanco app's own pages
    from app.blueprints import api, home
    app.register_blueprint(home.bp)
    app.register_blueprint(api.bp)

    with app.app_context():
        my_user = User.get_by_email(app.config["USER_FREE_EMAIL"])
        my_user.email = FREE_EMAIL
        get_db().session.commit()

    # the test profile turns registration off
    my_register = app.user_manager.USER_ENABLE_REGISTER
    app.user_manager.USER_ENABLE_REGISTER = True
    yield app
    app.user_manager.USER_ENABLE_REGISTER = my_register


@pytest.fixture()
def um(auth_app):
    return auth_app.user_manager


@contextmanager
def captured_mail(an_app):
    with an_app.extensions["mail"].record_messages() as my_outbox:
        yield my_outbox


def _cfg(a_key):
    return current_app.config[a_key]


def _login(a_client, an_identity, a_password, a_next=None):
    my_data = {"username": an_identity, "password": a_password}
    if a_next is not None:
        my_data["next"] = a_next
    return a_client.post("/user/sign-in", data=my_data)


def _is_signed_in(a_client):
    return a_client.get("/user/edit_user_profile").status_code == 200


def _link_from(a_message, a_path_prefix):
    my_match = re.search(r"https?://[^\s\"'<>]*" + re.escape(a_path_prefix) + r"[^\s\"'<>]*", a_message.body)
    assert my_match, a_message.body
    return urlsplit(my_match.group(0)).path


def _user(an_email):
    get_db().session.expire_all()
    return User.get_by_email(an_email)


# --------------------------------------------------------------- passwords

def test_hash_and_verify(um):
    my_hash = um.hash_password(NEW_PASSWORD)
    assert my_hash.startswith("$2b$")
    assert um.verify_password(NEW_PASSWORD, my_hash)
    assert not um.verify_password("wrong", my_hash)
    assert not um.verify_password("", my_hash)
    assert not um.verify_password(NEW_PASSWORD, "not-a-hash")


def test_verify_accepts_hashes_from_flask_user_and_passlib(um):
    assert um.verify_password("Legacy-Passw0rd", LEGACY_HASH_SHORT)
    assert um.verify_password("Ä" * 40, LEGACY_HASH_LONG)
    assert not um.verify_password("legacy-passw0rd", LEGACY_HASH_SHORT)


def test_long_passwords_hash_consistently(um):
    my_password = "x" * 100
    assert um.verify_password(my_password, um.hash_password(my_password))


def test_legacy_user_can_sign_in(auth_app, client):
    with auth_app.app_context():
        my_user = _user(FREE_EMAIL)
        my_user.password = LEGACY_HASH_SHORT
        get_db().session.commit()
        my_username = my_user.username

    assert _login(client, my_username, "Legacy-Passw0rd").status_code == 302
    assert _is_signed_in(client)


# ---------------------------------------------------------- sign in / out

def test_sign_in_page_renders(auth_app, client):
    my_response = client.get("/user/sign-in")
    assert my_response.status_code == 200
    assert b'name="password"' in my_response.data


@pytest.mark.parametrize("an_identity_key", ["USER_FREE_NAME", "EMAIL"])
def test_sign_in_with_username_or_email(auth_app, client, an_identity_key):
    with auth_app.app_context():
        my_identity = FREE_EMAIL if an_identity_key == "EMAIL" else _cfg(an_identity_key)
        my_password = _cfg("USER_FREE_PASS")

    my_response = _login(client, my_identity.upper() if "EMAIL" in an_identity_key else my_identity,
                         my_password, a_next="/ssk/tasks")
    assert my_response.status_code == 302
    assert my_response.headers["Location"] == "/ssk/tasks"
    assert _is_signed_in(client)


@pytest.mark.parametrize("an_identity", ["test_free", "nobody"])
def test_wrong_credentials_give_the_same_error(auth_app, client, an_identity):
    my_response = _login(client, an_identity, "wrong-password")
    assert my_response.status_code == 200
    assert b"Incorrect Username/Email and/or Password" in my_response.data
    assert not _is_signed_in(client)


def test_disabled_user_cannot_sign_in(auth_app, client):
    with auth_app.app_context():
        my_user = _user(FREE_EMAIL)
        my_user.active = False
        get_db().session.commit()
        my_username, my_password = my_user.username, _cfg("USER_FREE_PASS")

    _login(client, my_username, my_password)
    assert not _is_signed_in(client)


def test_unconfirmed_email_cannot_sign_in(auth_app, client):
    with auth_app.app_context():
        my_user = _user(FREE_EMAIL)
        my_user.email_confirmed_at = None
        get_db().session.commit()
        my_username, my_password = my_user.username, _cfg("USER_FREE_PASS")

    _login(client, my_username, my_password)
    assert not _is_signed_in(client)


def test_sign_out(auth_app, client):
    with auth_app.app_context():
        _login(client, _cfg("USER_FREE_NAME"), _cfg("USER_FREE_PASS"))
    assert _is_signed_in(client)
    assert client.get("/user/sign-out").status_code == 302
    assert not _is_signed_in(client)


def test_forged_session_is_rejected(auth_app, client):
    # a session that names the user but not their password fingerprint
    with auth_app.app_context():
        my_user_id = _user(_cfg("ADMIN_EMAIL")).id
    with client.session_transaction() as my_session:
        my_session["_user_id"] = str(my_user_id)
    assert not _is_signed_in(client)


# ----------------------------------------------------------- access rules

def test_anonymous_is_sent_to_sign_in(auth_app, client):
    my_response = client.get("/admin/")
    assert my_response.status_code == 302
    assert my_response.headers["Location"].startswith("/user/sign-in?next=")
    assert "%2Fadmin%2F" in my_response.headers["Location"] or "/admin/" in my_response.headers["Location"]


def test_non_admin_is_refused(auth_app, client):
    with auth_app.app_context():
        _login(client, _cfg("USER_FREE_NAME"), _cfg("USER_FREE_PASS"))
    my_response = client.get("/cmd/terminal")
    assert my_response.status_code == 302
    assert my_response.headers["Location"] == "/"


def test_admin_is_allowed(auth_app, client):
    with auth_app.app_context():
        _login(client, _cfg("ADMIN_NAME"), _cfg("ADMIN_PASS"))
    assert client.get("/cmd/terminal").status_code == 200


def test_has_roles(auth_app):
    with auth_app.app_context():
        my_admin = _user(_cfg("ADMIN_EMAIL"))
        assert my_admin.has_roles(_cfg("ADMIN_GROUP_NAME"))
        assert my_admin.has_roles(("nope", _cfg("ADMIN_GROUP_NAME")))
        assert not my_admin.has_roles(_cfg("ADMIN_GROUP_NAME"), "nope")


# ------------------------------------------------------------ registration

def test_register_confirm_and_sign_in(auth_app, client):
    with captured_mail(auth_app) as my_outbox:
        my_response = client.post("/user/register", data={
            "username": "newbie", "email": "newbie@example.com",
            "password": NEW_PASSWORD, "retype_password": NEW_PASSWORD})
    assert my_response.status_code == 302
    assert len(my_outbox) == 1 and my_outbox[0].recipients == ["newbie@example.com"]

    with auth_app.app_context():
        my_user = _user("newbie@example.com")
        assert my_user is not None and my_user.email_confirmed_at is None
        assert my_user.password != NEW_PASSWORD

    # not confirmed yet
    _login(client, "newbie", NEW_PASSWORD)
    assert not _is_signed_in(client)

    my_confirm_path = _link_from(my_outbox[0], "/user/confirm-email/")
    assert client.get(my_confirm_path).status_code == 302
    assert _is_signed_in(client)
    with auth_app.app_context():
        assert _user("newbie@example.com").email_confirmed_at is not None


@pytest.mark.parametrize("a_data, an_error", [
    ({"username": "ab", "email": "x@example.com", "password": NEW_PASSWORD, "retype_password": NEW_PASSWORD},
     b"at least 3 characters"),
    ({"username": "okname", "email": "x@example.com", "password": "weak", "retype_password": "weak"},
     b"at least 6 characters"),
    ({"username": "okname", "email": "x@example.com", "password": NEW_PASSWORD, "retype_password": "Other1x"},
     b"did not match"),
    ({"username": "test_free", "email": "x@example.com", "password": NEW_PASSWORD, "retype_password": NEW_PASSWORD},
     b"Username is already in use"),
    ({"username": "okname", "email": "FREE@example.com", "password": NEW_PASSWORD, "retype_password": NEW_PASSWORD},
     b"Email is already in use"),
])
def test_register_validation(auth_app, client, a_data, an_error):
    my_response = client.post("/user/register", data=a_data)
    assert my_response.status_code == 200
    assert an_error in my_response.data


def test_confirm_link_is_tied_to_the_address(auth_app, client, um):
    with auth_app.test_request_context():
        my_user = _user(FREE_EMAIL)
        my_token = um.generate_token("confirm-email", my_user.id, "someone-else@example.com")
    client.get("/user/confirm-email/" + my_token)
    assert not _is_signed_in(client)


def test_tampered_tokens_are_rejected(auth_app, client):
    assert client.get("/user/confirm-email/garbage").status_code == 302
    assert client.get("/user/reset-password/garbage").status_code == 302
    assert not _is_signed_in(client)


def test_register_disabled(auth_app, client, um):
    um.USER_ENABLE_REGISTER = False
    # ssk's request_error handler reports every 4xx as 400
    assert client.get("/user/register").status_code == 400


def test_invite_only_registration(auth_app, client, um):
    with auth_app.app_context():
        _login(client, _cfg("ADMIN_NAME"), _cfg("ADMIN_PASS"))
    um.USER_REQUIRE_INVITATION = True
    um.USER_ENABLE_INVITE_USER = True
    try:
        assert client.get("/user/register").status_code == 302

        with captured_mail(auth_app) as my_outbox:
            assert client.post("/user/invite", data={"email": "guest@example.com"}).status_code == 302
        my_register_path = _link_from(my_outbox[0], "/user/register")
        my_token = re.search(r"token=([^&\s\"'<>]+)", my_outbox[0].body).group(1)
        assert my_register_path == "/user/register"

        client.get("/user/sign-out")
        with captured_mail(auth_app):
            my_response = client.post("/user/register?token=" + my_token, data={
                "username": "guest", "email": "guest@example.com", "invite_token": my_token,
                "password": NEW_PASSWORD, "retype_password": NEW_PASSWORD})
        assert my_response.status_code == 302
        # the invitation proved the address, so the guest is signed in straight away
        assert _is_signed_in(client)
    finally:
        um.USER_REQUIRE_INVITATION = False
        um.USER_ENABLE_INVITE_USER = False


# ---------------------------------------------------------- password reset

def test_forgot_and_reset_password(auth_app, client):
    with auth_app.app_context():
        my_email, my_username, my_old = FREE_EMAIL, _cfg("USER_FREE_NAME"), _cfg("USER_FREE_PASS")

    with captured_mail(auth_app) as my_outbox:
        assert client.post("/user/forgot-password", data={"email": my_email}).status_code == 302
    my_reset_path = _link_from(my_outbox[0], "/user/reset-password/")

    assert client.get(my_reset_path).status_code == 200
    with captured_mail(auth_app):
        my_response = client.post(my_reset_path, data={"new_password": NEW_PASSWORD,
                                                       "retype_password": NEW_PASSWORD})
    assert my_response.status_code == 302
    assert _is_signed_in(client)

    client.get("/user/sign-out")
    _login(client, my_username, my_old)
    assert not _is_signed_in(client)
    _login(client, my_username, NEW_PASSWORD)
    assert _is_signed_in(client)

    # the link only works once
    client.get("/user/sign-out")
    my_again = client.post(my_reset_path, data={"new_password": "Another1x", "retype_password": "Another1x"})
    assert my_again.status_code == 302 and my_again.headers["Location"] == "/user/sign-in"
    _login(client, my_username, "Another1x")
    assert not _is_signed_in(client)


def test_forgot_password_does_not_reveal_unknown_addresses(auth_app, client):
    with captured_mail(auth_app) as my_outbox:
        my_response = client.post("/user/forgot-password", data={"email": "nobody@example.com"})
    assert my_response.status_code == 302
    assert my_outbox == []


# ----------------------------------------------------------- account pages

def test_change_password_signs_out_other_sessions(auth_app):
    my_first, my_second = auth_app.test_client(), auth_app.test_client()
    with auth_app.app_context():
        my_username, my_old = _cfg("USER_FREE_NAME"), _cfg("USER_FREE_PASS")
    _login(my_first, my_username, my_old)
    _login(my_second, my_username, my_old)

    my_wrong = my_first.post("/user/change-password", data={
        "old_password": "wrong", "new_password": NEW_PASSWORD, "retype_password": NEW_PASSWORD})
    assert b"Old Password is incorrect" in my_wrong.data

    with captured_mail(auth_app) as my_outbox:
        my_response = my_first.post("/user/change-password", data={
            "old_password": my_old, "new_password": NEW_PASSWORD, "retype_password": NEW_PASSWORD})
    assert my_response.status_code == 302
    assert len(my_outbox) == 1

    assert _is_signed_in(my_first)
    assert not _is_signed_in(my_second)


def test_change_username(auth_app, client):
    with auth_app.app_context():
        _login(client, _cfg("USER_FREE_NAME"), _cfg("USER_FREE_PASS"))
        my_password = _cfg("USER_FREE_PASS")
    with captured_mail(auth_app):
        my_response = client.post("/user/change-username", data={"new_username": "renamed",
                                                                  "old_password": my_password})
    assert my_response.status_code == 302
    with auth_app.app_context():
        assert _user(FREE_EMAIL).username == "renamed"


def test_edit_profile(auth_app, client):
    with auth_app.app_context():
        _login(client, _cfg("USER_FREE_NAME"), _cfg("USER_FREE_PASS"))
    assert client.post("/user/edit_user_profile", data={"first_name": "Ada", "last_name": "L"}).status_code == 302
    with auth_app.app_context():
        my_user = _user(FREE_EMAIL)
        assert (my_user.first_name, my_user.last_name) == ("Ada", "L")


@pytest.mark.parametrize("a_path", ["/user/register", "/user/forgot-password", "/user/resend-email-confirmation"])
def test_public_pages_render(auth_app, client, a_path):
    assert client.get(a_path).status_code == 200


@pytest.mark.parametrize("a_path", ["/user/change-password", "/user/change-username", "/user/edit_user_profile"])
def test_account_pages_render(auth_app, client, a_path):
    with auth_app.app_context():
        _login(client, _cfg("USER_FREE_NAME"), _cfg("USER_FREE_PASS"))
    assert client.get(a_path).status_code == 200
