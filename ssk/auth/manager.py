#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#

import datetime
import hashlib
import hmac
from urllib.parse import urlsplit, urlunsplit

import bcrypt
from flask import current_app, render_template, session
from flask_login import LoginManager
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy import func
from wtforms import ValidationError

from .settings import DEFAULTS

BCRYPT_MAX_BYTES = 72

# characters a browser drops or treats specially at the start of a URL
_URL_IGNORED_CHARS = ''.join(chr(my_code) for my_code in range(0x21))


class ConfigError(Exception):
    pass


def truncate_password(a_password):
    """Truncate to bcrypt's 72-byte limit without splitting a UTF-8 character."""
    if isinstance(a_password, str):
        my_bytes = a_password.encode('utf-8')
        if len(my_bytes) > BCRYPT_MAX_BYTES:
            return my_bytes[:BCRYPT_MAX_BYTES].decode('utf-8', errors='ignore')
    return a_password


class UserManager:
    """Users, passwords, tokens and auth emails.

    Drop-in for the parts of Flask-User 1.0 that Soseki used: same USER_* settings, URLs,
    endpoint names (user.login, ...) and templates, and the same API (hash_password,
    verify_password, make_safe_url, password_validator, ...).
    """

    def __init__(self, app=None, db=None, UserClass=None, UserInvitationClass=None, RoleClass=None):
        self.app = None
        if app is not None:
            self.init_app(app, db, UserClass, UserInvitationClass, RoleClass)

    # ------------------------------------------------------------------ setup

    def init_app(self, app, db, UserClass, UserInvitationClass=None, RoleClass=None):
        self.app = app
        self.db = db
        self.UserClass = UserClass
        self.UserInvitationClass = UserInvitationClass
        self.RoleClass = RoleClass
        app.user_manager = self

        for my_key, my_default in DEFAULTS.items():
            setattr(self, my_key, app.config.get(my_key, my_default))
        self._check_settings(app)

        if not app.config.get('SECRET_KEY'):
            raise ConfigError('SECRET_KEY is missing.')

        if self.USER_USER_SESSION_EXPIRATION:
            app.permanent_session_lifetime = datetime.timedelta(seconds=self.USER_USER_SESSION_EXPIRATION)

            @app.before_request
            def advance_session_timeout():
                session.permanent = True
                session.modified = True

        if 'mail' not in app.extensions:
            from flask_mail import Mail
            Mail(app)

        self.login_manager = LoginManager(app)
        self.login_manager.login_view = 'user.login'
        self.login_manager.user_loader(self.load_user)

        # the templates use {% trans %}; without Flask-Babel this renders the text unchanged
        if 'jinja2.ext.i18n' not in app.jinja_env.extensions:
            app.jinja_env.add_extension('jinja2.ext.i18n')
            app.jinja_env.install_null_translations()

        def auth_context_processor():
            return dict(user_manager=current_app.user_manager, call_or_get=call_or_get)
        app.context_processor(auth_context_processor)

        from .views import create_blueprint
        app.register_blueprint(create_blueprint(self))

    def _check_settings(self, app):
        if not self.USER_EMAIL_SENDER_EMAIL:
            my_default_sender = app.config.get('MAIL_DEFAULT_SENDER') or ''
            if isinstance(my_default_sender, str) and my_default_sender.endswith('>') and '<' in my_default_sender:
                my_start = my_default_sender.rfind('<')
                self.USER_EMAIL_SENDER_EMAIL = my_default_sender[my_start + 1:-1]
                if not self.USER_EMAIL_SENDER_NAME:
                    self.USER_EMAIL_SENDER_NAME = my_default_sender[:my_start].strip(' "')
            else:
                self.USER_EMAIL_SENDER_EMAIL = my_default_sender
        if not self.USER_EMAIL_SENDER_NAME:
            self.USER_EMAIL_SENDER_NAME = self.USER_APP_NAME

        if self.USER_ENABLE_EMAIL and '@' not in (self.USER_EMAIL_SENDER_EMAIL or ''):
            raise ConfigError('USER_EMAIL_SENDER_EMAIL is missing or invalid while USER_ENABLE_EMAIL is True.')
        if self.USER_ENABLE_INVITE_USER and self.UserInvitationClass is None:
            raise ConfigError('USER_ENABLE_INVITE_USER needs a UserInvitationClass.')

        if not self.USER_ENABLE_USERNAME and not self.USER_ENABLE_EMAIL:
            self.USER_ENABLE_REGISTER = False
        if not self.USER_ENABLE_EMAIL:
            self.USER_ENABLE_CONFIRM_EMAIL = False
            self.USER_ENABLE_FORGOT_PASSWORD = False
            self.USER_SEND_PASSWORD_CHANGED_EMAIL = False
            self.USER_SEND_REGISTERED_EMAIL = False
            self.USER_SEND_USERNAME_CHANGED_EMAIL = False
            self.USER_REQUIRE_INVITATION = False
        if not self.USER_ENABLE_USERNAME:
            self.USER_ENABLE_CHANGE_USERNAME = False

    # -------------------------------------------------------------- passwords

    def hash_password(self, a_password):
        my_bytes = truncate_password(a_password).encode('utf-8')
        my_salt = bcrypt.gensalt(rounds=int(self.USER_BCRYPT_ROUNDS))
        return bcrypt.hashpw(my_bytes, my_salt).decode('utf-8')

    def verify_password(self, a_password, a_password_hash):
        """Check a password against a bcrypt hash, including hashes made by Flask-User/passlib."""
        if not a_password or not a_password_hash:
            return False

        my_hash = a_password_hash.encode('utf-8') if isinstance(a_password_hash, str) else a_password_hash
        my_candidates = [truncate_password(a_password).encode('utf-8')]
        my_raw = a_password.encode('utf-8')
        if len(my_raw) > BCRYPT_MAX_BYTES and my_raw[:BCRYPT_MAX_BYTES] not in my_candidates:
            # passlib cut long passwords at exactly 72 bytes, even inside a UTF-8 character
            my_candidates.append(my_raw[:BCRYPT_MAX_BYTES])

        for my_candidate in my_candidates:
            try:
                if bcrypt.checkpw(my_candidate, my_hash):
                    return True
            except ValueError:
                return False
        return False

    def dummy_password_hash(self):
        """A real bcrypt hash of a random password, so a login for an unknown user costs the same
        time as one with a wrong password and response times don't reveal which accounts exist."""
        if getattr(self, '_dummy_password_hash', None) is None:
            import secrets
            self._dummy_password_hash = self.hash_password(secrets.token_urlsafe(16))
        return self._dummy_password_hash

    def password_validator(self, form, field):
        my_password = field.data or ''
        my_valid = (len(my_password) >= 6
                    and any(my_char.islower() for my_char in my_password)
                    and any(my_char.isupper() for my_char in my_password)
                    and any(my_char.isdigit() for my_char in my_password))
        if not my_valid:
            raise ValidationError('Password must have at least 6 characters with one lowercase letter, '
                                  'one uppercase letter and one number')

    def username_validator(self, form, field):
        my_username = field.data or ''
        if len(my_username) < 3:
            raise ValidationError('Username must be at least 3 characters long')
        my_valid_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._')
        if not set(my_username) <= my_valid_chars:
            raise ValidationError("Username may only contain letters, numbers, '-', '.' and '_'")

    # ----------------------------------------------------------------- tokens

    def _serializer(self, a_purpose):
        return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt='ssk-auth-' + a_purpose)

    def generate_token(self, a_purpose, *a_items):
        return self._serializer(a_purpose).dumps(list(a_items))

    def verify_token(self, a_purpose, a_token, a_max_age=None):
        """Return the token's items, or None if it is invalid, tampered with or expired."""
        try:
            return self._serializer(a_purpose).loads(a_token, max_age=a_max_age)
        except (BadSignature, SignatureExpired):
            return None

    def password_fingerprint(self, a_user):
        """Short HMAC of the password hash: changes whenever the password changes."""
        my_key = current_app.config['SECRET_KEY']
        my_key = my_key.encode('utf-8') if isinstance(my_key, str) else my_key
        return hmac.new(my_key, (a_user.password or '').encode('utf-8'), hashlib.sha256).hexdigest()[:16]

    # ---------------------------------------------------------------- session

    def load_user(self, a_user_id):
        """Flask-Login loader. The id carries a password fingerprint, so changing the
        password signs out every other session and invalidates remember-me cookies."""
        my_id, _, my_fingerprint = (a_user_id or '').partition('|')
        if not my_id.isdigit():
            return None
        my_user = self.db.session.get(self.UserClass, int(my_id))
        if my_user is None or not hmac.compare_digest(self.password_fingerprint(my_user), my_fingerprint):
            return None
        return my_user

    # ----------------------------------------------------------------- lookup

    def find_user_by_username(self, a_username):
        if not a_username:
            return None
        return self.UserClass.query.filter(func.lower(self.UserClass.username) == a_username.lower()).first()

    def find_user_by_email(self, a_email):
        if not a_email:
            return None
        return self.UserClass.query.filter(func.lower(self.UserClass.email) == a_email.lower()).first()

    def username_is_available(self, a_username):
        return self.find_user_by_username(a_username) is None

    def email_is_available(self, a_email):
        return self.find_user_by_email(a_email) is None

    # ------------------------------------------------------------------- URLs

    def make_safe_url(self, a_url):
        """Reduce a URL to a local path, so redirects can't leave the site.

        Strips scheme and host, then also handles what browsers do with what's left:
        tab/CR/LF are ignored, leading control characters and spaces are stripped,
        '\\' means '/', and a leading '//' starts a new host (CVE-2021-23401).
        """
        my_parts = list(urlsplit(a_url or ''))
        my_parts[0] = ''
        my_parts[1] = ''
        my_safe_url = urlunsplit(my_parts)

        for my_char in '\t\r\n':
            my_safe_url = my_safe_url.replace(my_char, '')
        my_safe_url = my_safe_url.lstrip(_URL_IGNORED_CHARS).replace('\\', '/')
        if my_safe_url.startswith('//'):
            my_safe_url = '/' + my_safe_url.lstrip('/')
        return my_safe_url

    # ----------------------------------------------------------------- emails

    def send_email(self, a_recipient, a_user, a_template, **a_kwargs):
        """Render <template>_subject.txt / _message.html / _message.txt and send them."""
        if not self.USER_ENABLE_EMAIL:
            return
        from flask_mail import Message

        a_kwargs.update(app_name=self.USER_APP_NAME, email=a_recipient, user=a_user, user_manager=self)
        my_subject = render_template(a_template + '_subject.txt', **a_kwargs).replace('\n', ' ').replace('\r', ' ')
        my_html = render_template(a_template + '_message.html', **a_kwargs)
        my_text = render_template(a_template + '_message.txt', **a_kwargs)

        my_sender = (self.USER_EMAIL_SENDER_NAME, self.USER_EMAIL_SENDER_EMAIL) \
            if self.USER_EMAIL_SENDER_NAME else self.USER_EMAIL_SENDER_EMAIL
        my_message = Message(my_subject, sender=my_sender, recipients=[a_recipient], html=my_html, body=my_text)
        current_app.extensions['mail'].send(my_message)


def call_or_get(a_function_or_property):
    return a_function_or_property() if callable(a_function_or_property) else a_function_or_property
