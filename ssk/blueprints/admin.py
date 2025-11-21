#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


import os.path

from flask import (Blueprint, current_app, send_file)
from flask import render_template
from flask_login import current_user
from flask_user import roles_required

from .. import get_db
from ..models.audit import Audit
from ..utils import get_timestamp_str
from ..ssk_consts import SSK_ADMIN_GROUP

from ssk.blueprints.admin_handler import AdminHandler

bp = Blueprint('admin', __name__, url_prefix='/admin')


@bp.route('/', methods=['GET'])
@roles_required(SSK_ADMIN_GROUP)
def index():
    return render_template('ssk/home.html', timestamp=get_timestamp_str())


@bp.route('/log_download', methods=['GET'])
@roles_required(SSK_ADMIN_GROUP)
def log_download():
    my_current = os.getcwd()
    my_log_path = os.path.join(my_current, current_app.config["LOG_FILE"])

    my_status = "OK"
    if not os.path.exists(my_log_path):
        my_status = "NOK"

    my_audit = Audit()
    my_audit.status = my_status
    my_audit.category = "LOG"
    my_audit.by_user = current_user.email
    my_audit.description = "log {}".format(my_log_path)
    get_db().session.add(my_audit)
    get_db().session.commit()

    if my_status == "OK":
        return send_file(my_log_path, as_attachment=True)

    return render_template('ssk/home.html', timestamp=get_timestamp_str())


@bp.route('/system_chart', methods=['GET'])
@roles_required(SSK_ADMIN_GROUP)
def system_chart():
    my_file, my_to_plot = AdminHandler.system_chart()

    return render_template(my_file, system_status=my_to_plot, admin_group_name=SSK_ADMIN_GROUP)


@bp.route('/system_perf', methods=['GET'])
@roles_required(SSK_ADMIN_GROUP)
def system_perf():
    my_file, my_stats = AdminHandler.system_stats()

    return render_template(my_file,
                           system_perf=my_stats["plot"],
                           daily_stats=my_stats["stats"],
                           daily_perf=my_stats["perf"],
                           all_pages=my_stats["all_pages"],
                           all_days=my_stats["all_days"],
                           db_stats=my_stats["db_stats"],
                           db_tables=my_stats["db_tables"],
                           db_days=my_stats["db_days"],
                           admin_group_name=SSK_ADMIN_GROUP)
