#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


from flask import render_template
from flask_login import current_user

import ssk


class WebGate:
    PAGE_CLOSED = "ssk/closed.html"
    NOT_FOUND = "ssk/not_found.html"

    @staticmethod
    def is_closed():
        if not ssk.AppSettings().get_setting("WEBSITE_OPEN"):
            if current_user.is_anonymous or not current_user.is_admin():
                return True

        return False

    @staticmethod
    def render_closed():
        return render_template(WebGate.PAGE_CLOSED, admin_group_name=ssk.SSK_ADMIN_GROUP)

    @staticmethod
    def render_notfound():
        return render_template(WebGate.NOT_FOUND, admin_group_name=ssk.SSK_ADMIN_GROUP)
