#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


from flask import current_app, render_template

from flask_user import current_user
from flask_mail import Mail, Message

from .app_settings import AppSettings
from ..models.audit import Audit


class EmailMgr:
    _db_session = None

    def __init__(self, a_db_session):
        self._db_session = a_db_session

    def sendit(self, a_message):
        my_email_off = AppSettings().get_setting("IS_OFFLINE")
        if my_email_off is None or my_email_off is False:
            my_mail = Mail(current_app)
            my_mail.send(a_message)

    def send_test(self, a_from, a_to):
        try:
            my_mail_mesg = Message('Test email', sender=a_from, recipients=[a_to])

            my_render_args = {'app_name': current_app.config["USER_APP_NAME"],
                              'app_version': current_app.config["USER_APP_VERSION"], 'user': current_user}

            my_txt_message = render_template('ssk/emails/test.txt', **my_render_args)
            my_html_message = render_template('ssk/emails/test.html', **my_render_args)

            my_mail_mesg.body = my_txt_message
            my_mail_mesg.html = my_html_message

            self.sendit(my_mail_mesg)

            # keeping track of things
            my_audit = Audit()
            my_audit.category = "EMAIL"
            my_audit.by_user = "admin"
            my_audit.status = "OK"
            my_audit.description = "Test email sent from {} to {}".format(a_from, a_to)
        except Exception as ex:
            my_audit = Audit()
            my_audit.category = "EMAIL"
            my_audit.by_user = "admin"
            my_audit.status = "NOK"
            my_audit.description = "Error: Test email sent from {} to {} failed {}".format(a_from, a_to, ex)

        self._db_session.add(my_audit)
        return my_audit