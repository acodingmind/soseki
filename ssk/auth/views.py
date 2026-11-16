#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#

from datetime import datetime
from urllib.parse import quote, unquote

from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_user, logout_user

from . import forms
from .decorators import login_required


def create_blueprint(um):
    """Build the 'user' blueprint for a UserManager `um`; endpoint names match Flask-User's."""
    bp = Blueprint('user', __name__)

    # ---------------------------------------------------------------- helpers

    def endpoint_url(an_endpoint):
        return url_for(an_endpoint) if an_endpoint else '/'

    def safe_next_url(a_param, a_default_endpoint):
        if a_param in request.args:
            return um.make_safe_url(unquote(request.args[a_param]))
        return endpoint_url(a_default_endpoint)

    def login_then(a_next_url):
        return redirect(url_for('user.login') + '?next=' + quote(a_next_url))

    def has_confirmed_email(a_user):
        return bool(a_user.email_confirmed_at)

    def do_login(a_user, a_next_url, a_remember=False):
        if not a_user.active:
            flash('Your account has not been enabled.', 'error')
            return redirect(url_for('user.login'))
        if um.USER_ENABLE_EMAIL and um.USER_ENABLE_CONFIRM_EMAIL and \
                not um.USER_ALLOW_LOGIN_WITHOUT_CONFIRMED_EMAIL and not has_confirmed_email(a_user):
            flash('Your email address has not yet been confirmed. Check your email Inbox and Spam folders '
                  'for the confirmation email, or re-send it from the sign-in page.', 'error')
            return redirect(url_for('user.login'))
        login_user(a_user, remember=bool(a_remember))
        flash('You have signed in successfully.', 'success')
        return redirect(a_next_url)

    def save(*an_objects):
        for my_object in an_objects:
            um.db.session.add(my_object)
        um.db.session.commit()

    def send_confirm_email(a_user):
        if um.USER_ENABLE_EMAIL and um.USER_ENABLE_CONFIRM_EMAIL:
            my_token = um.generate_token('confirm-email', a_user.id, a_user.email)
            um.send_email(a_user.email, a_user, um.USER_CONFIRM_EMAIL_TEMPLATE,
                          confirm_email_link=url_for('user.confirm_email', token=my_token, _external=True))
            flash('A confirmation email has been sent to {} with instructions to complete your '
                  'registration.'.format(a_user.email), 'success')

    def feature(a_setting):
        if not getattr(um, a_setting):
            abort(404)

    # ----------------------------------------------------------- sign in/out

    @bp.route(um.USER_LOGIN_URL, endpoint='login', methods=['GET', 'POST'])
    def login():
        my_next = safe_next_url('next', um.USER_AFTER_LOGIN_ENDPOINT)
        my_reg_next = safe_next_url('reg_next', um.USER_AFTER_REGISTER_ENDPOINT)
        if current_user.is_authenticated and um.USER_AUTO_LOGIN_AT_LOGIN:
            return redirect(my_next)

        my_login_form = forms.LoginForm(request.form)
        my_register_form = forms.RegisterForm()
        if request.method != 'POST':
            my_login_form.next.data = my_register_form.next.data = my_next
            my_login_form.reg_next.data = my_register_form.reg_next.data = my_reg_next

        if request.method == 'POST' and my_login_form.validate():
            return do_login(my_login_form.user, um.make_safe_url(my_login_form.next.data),
                            my_login_form.remember_me.data and um.USER_ENABLE_REMEMBER_ME)

        return render_template(um.USER_LOGIN_TEMPLATE, form=my_login_form,
                               login_form=my_login_form, register_form=my_register_form)

    @bp.route(um.USER_LOGOUT_URL, endpoint='logout', methods=['GET', 'POST'])
    def logout():
        logout_user()
        flash('You have signed out successfully.', 'success')
        return redirect(safe_next_url('next', um.USER_AFTER_LOGOUT_ENDPOINT))

    # ------------------------------------------------------------- register

    @bp.route(um.USER_REGISTER_URL, endpoint='register', methods=['GET', 'POST'])
    def register():
        feature('USER_ENABLE_REGISTER')
        my_next = safe_next_url('next', um.USER_AFTER_LOGIN_ENDPOINT)
        my_reg_next = safe_next_url('reg_next', um.USER_AFTER_REGISTER_ENDPOINT)
        my_login_form = forms.LoginForm()
        my_register_form = forms.RegisterForm(request.form)

        my_invite_token = request.values.get('token')
        if um.USER_REQUIRE_INVITATION and not my_invite_token:
            flash('Registration is invite only', 'error')
            return redirect(url_for('user.login'))

        my_invitation = None
        if my_invite_token and um.UserInvitationClass is not None:
            my_items = um.verify_token('invite', my_invite_token, um.USER_INVITE_EXPIRATION)
            if my_items:
                my_invitation = um.db.session.get(um.UserInvitationClass, my_items[0])
            if my_invitation is None:
                flash('Invalid invitation token', 'error')
                return redirect(url_for('user.login'))
            my_register_form.invite_token.data = my_invite_token

        if request.method != 'POST':
            my_login_form.next.data = my_register_form.next.data = my_next
            my_login_form.reg_next.data = my_register_form.reg_next.data = my_reg_next
            if my_invitation is not None:
                my_register_form.email.data = my_invitation.email

        if request.method == 'POST' and my_register_form.validate():
            my_user = um.UserClass()
            if um.USER_ENABLE_USERNAME:
                my_user.username = my_register_form.username.data
            if um.USER_ENABLE_EMAIL:
                my_user.email = my_register_form.email.data
            my_user.password = um.hash_password(my_register_form.password.data)
            my_user.active = True

            my_request_confirmation = um.USER_ENABLE_CONFIRM_EMAIL
            if my_invitation is not None and my_user.email and \
                    my_invitation.email.lower() == my_user.email.lower():
                # the invitation link already proved the address
                my_user.email_confirmed_at = datetime.now()
                my_request_confirmation = False
            save(my_user)

            if um.USER_ENABLE_EMAIL and um.USER_SEND_REGISTERED_EMAIL:
                my_link = None
                if my_request_confirmation:
                    my_token = um.generate_token('confirm-email', my_user.id, my_user.email)
                    my_link = url_for('user.confirm_email', token=my_token, _external=True)
                try:
                    um.send_email(my_user.email, my_user, um.USER_REGISTERED_EMAIL_TEMPLATE,
                                  confirm_email_link=my_link)
                except Exception:
                    um.db.session.delete(my_user)
                    um.db.session.commit()
                    raise
                if my_request_confirmation:
                    flash('A confirmation email has been sent to {} with instructions to complete your '
                          'registration.'.format(my_user.email), 'success')
                else:
                    flash('You have registered successfully.', 'success')

            if um.USER_ENABLE_CONFIRM_EMAIL and my_request_confirmation:
                return redirect(um.make_safe_url(my_register_form.reg_next.data) or '/')

            if 'reg_next' in request.args:
                my_after = um.make_safe_url(my_register_form.reg_next.data)
            else:
                my_after = endpoint_url(um.USER_AFTER_CONFIRM_ENDPOINT)
            if um.USER_AUTO_LOGIN_AFTER_REGISTER:
                return do_login(my_user, my_after)
            return login_then(my_after)

        return render_template(um.USER_REGISTER_TEMPLATE, form=my_register_form,
                               login_form=my_login_form, register_form=my_register_form)

    # ---------------------------------------------------- email confirmation

    @bp.route(um.USER_CONFIRM_EMAIL_URL, endpoint='confirm_email')
    def confirm_email(token):
        feature('USER_ENABLE_CONFIRM_EMAIL')
        my_items = um.verify_token('confirm-email', token, um.USER_CONFIRM_EMAIL_EXPIRATION)
        my_user = um.db.session.get(um.UserClass, my_items[0]) if my_items else None
        # the token is tied to the address it was sent to
        if my_user is None or (my_user.email or '').lower() != (my_items[1] or '').lower():
            flash('Invalid confirmation token.', 'error')
            return redirect(url_for('user.login'))

        my_user.email_confirmed_at = datetime.now()
        save(my_user)
        flash('Your email has been confirmed.', 'success')

        my_next = safe_next_url('next', um.USER_AFTER_CONFIRM_ENDPOINT)
        if um.USER_AUTO_LOGIN_AFTER_CONFIRM:
            return do_login(my_user, my_next)
        return login_then(my_next)

    @bp.route(um.USER_RESEND_EMAIL_CONFIRMATION_URL, endpoint='resend_email_confirmation', methods=['GET', 'POST'])
    def resend_email_confirmation():
        feature('USER_ENABLE_CONFIRM_EMAIL')
        my_form = forms.ResendEmailConfirmationForm(request.form)
        if request.method == 'POST' and my_form.validate():
            my_user = um.find_user_by_email(my_form.email.data)
            if my_user is not None and not my_user.email_confirmed_at:
                send_confirm_email(my_user)
            return redirect(endpoint_url(um.USER_AFTER_RESEND_EMAIL_CONFIRMATION_ENDPOINT))
        return render_template(um.USER_RESEND_CONFIRM_EMAIL_TEMPLATE, form=my_form)

    # ------------------------------------------------------- password reset

    @bp.route(um.USER_FORGOT_PASSWORD_URL, endpoint='forgot_password', methods=['GET', 'POST'])
    def forgot_password():
        feature('USER_ENABLE_FORGOT_PASSWORD')
        my_form = forms.ForgotPasswordForm(request.form)
        if request.method == 'POST' and my_form.validate():
            my_email = my_form.email.data
            my_user = um.find_user_by_email(my_email)
            if my_user is not None:
                # tied to the current password, so the link stops working once it has been used
                my_token = um.generate_token('reset-password', my_user.id, um.password_fingerprint(my_user))
                um.send_email(my_user.email, my_user, um.USER_RESET_PASSWORD_EMAIL_TEMPLATE,
                              reset_password_link=url_for('user.reset_password', token=my_token, _external=True))
            # same message whether or not the address exists
            flash("A reset password email has been sent to '{}'. Open that email and follow the instructions "
                  "to reset your password.".format(my_email), 'success')
            return redirect(endpoint_url(um.USER_AFTER_FORGOT_PASSWORD_ENDPOINT))
        return render_template(um.USER_FORGOT_PASSWORD_TEMPLATE, form=my_form)

    @bp.route(um.USER_RESET_PASSWORD_URL, endpoint='reset_password', methods=['GET', 'POST'])
    def reset_password(token):
        feature('USER_ENABLE_FORGOT_PASSWORD')
        if current_user.is_authenticated:
            logout_user()

        my_items = um.verify_token('reset-password', token, um.USER_RESET_PASSWORD_EXPIRATION)
        my_user = um.db.session.get(um.UserClass, my_items[0]) if my_items else None
        if my_user is None or my_items[1] != um.password_fingerprint(my_user):
            flash('Your reset password token is invalid.', 'error')
            return redirect(url_for('user.login'))

        my_form = forms.ResetPasswordForm(request.form)
        if request.method == 'POST' and my_form.validate():
            my_user.password = um.hash_password(my_form.new_password.data)
            # the link arrived by email, which proves the address
            if not my_user.email_confirmed_at:
                my_user.email_confirmed_at = datetime.now()
            save(my_user)
            if um.USER_SEND_PASSWORD_CHANGED_EMAIL:
                um.send_email(my_user.email, my_user, um.USER_PASSWORD_CHANGED_EMAIL_TEMPLATE)
            flash('Your password has been reset successfully.', 'success')

            my_next = safe_next_url('next', um.USER_AFTER_RESET_PASSWORD_ENDPOINT)
            if um.USER_AUTO_LOGIN_AFTER_RESET_PASSWORD:
                return do_login(my_user, my_next)
            return login_then(my_next)
        return render_template(um.USER_RESET_PASSWORD_TEMPLATE, form=my_form)

    # ------------------------------------------------------- account pages

    @bp.route(um.USER_CHANGE_PASSWORD_URL, endpoint='change_password', methods=['GET', 'POST'])
    @login_required
    def change_password():
        feature('USER_ENABLE_CHANGE_PASSWORD')
        my_form = forms.ChangePasswordForm(request.form)
        if request.method == 'POST' and my_form.validate():
            my_user = current_user._get_current_object()
            my_user.password = um.hash_password(my_form.new_password.data)
            save(my_user)
            # the session id includes a password fingerprint: refresh it so this session stays signed in
            # (other sessions and remember-me cookies stop working, which is the point)
            session['_user_id'] = my_user.get_id()
            if um.USER_SEND_PASSWORD_CHANGED_EMAIL:
                um.send_email(my_user.email, my_user, um.USER_PASSWORD_CHANGED_EMAIL_TEMPLATE)
            flash('Your password has been changed successfully.', 'success')
            return redirect(safe_next_url('next', um.USER_AFTER_CHANGE_PASSWORD_ENDPOINT))
        return render_template(um.USER_CHANGE_PASSWORD_TEMPLATE, form=my_form)

    @bp.route(um.USER_CHANGE_USERNAME_URL, endpoint='change_username', methods=['GET', 'POST'])
    @login_required
    def change_username():
        feature('USER_ENABLE_CHANGE_USERNAME')
        my_form = forms.ChangeUsernameForm(request.form)
        if request.method == 'POST' and my_form.validate():
            my_user = current_user._get_current_object()
            my_user.username = my_form.new_username.data
            save(my_user)
            if um.USER_SEND_USERNAME_CHANGED_EMAIL:
                um.send_email(my_user.email, my_user, um.USER_USERNAME_CHANGED_EMAIL_TEMPLATE)
            flash("Your username has been changed to '{}'.".format(my_user.username), 'success')
            return redirect(safe_next_url('next', um.USER_AFTER_CHANGE_USERNAME_ENDPOINT))
        return render_template(um.USER_CHANGE_USERNAME_TEMPLATE, form=my_form)

    @bp.route(um.USER_EDIT_USER_PROFILE_URL, endpoint='edit_user_profile', methods=['GET', 'POST'])
    @login_required
    def edit_user_profile():
        my_user = current_user._get_current_object()
        my_form = forms.EditUserProfileForm(request.form, obj=my_user)
        if request.method == 'POST' and my_form.validate():
            my_user.first_name = my_form.first_name.data
            my_user.last_name = my_form.last_name.data
            save(my_user)
            return redirect(endpoint_url(um.USER_AFTER_EDIT_USER_PROFILE_ENDPOINT))
        return render_template(um.USER_EDIT_USER_PROFILE_TEMPLATE, form=my_form)

    @bp.route(um.USER_INVITE_USER_URL, endpoint='invite_user', methods=['GET', 'POST'])
    @login_required
    def invite_user():
        feature('USER_ENABLE_INVITE_USER')
        my_form = forms.InviteUserForm(request.form)
        if request.method == 'POST' and my_form.validate():
            my_email = my_form.email.data
            if um.find_user_by_email(my_email) is not None:
                flash('User with that email has already registered', 'error')
                return redirect(url_for('user.invite_user'))

            my_invitation = um.UserInvitationClass(email=my_email, invited_by_user_id=current_user.id)
            save(my_invitation)
            try:
                my_token = um.generate_token('invite', my_invitation.id)
                um.send_email(my_email, um.UserClass(email=my_email), um.USER_INVITE_USER_EMAIL_TEMPLATE,
                              accept_invitation_link=url_for('user.register', token=my_token, _external=True),
                              invited_by_user=current_user)
            except Exception:
                um.db.session.delete(my_invitation)
                um.db.session.commit()
                raise
            flash('Invitation has been sent.', 'success')
            return redirect(safe_next_url('next', um.USER_AFTER_INVITE_ENDPOINT))
        return render_template(um.USER_INVITE_USER_TEMPLATE, form=my_form)

    return bp
