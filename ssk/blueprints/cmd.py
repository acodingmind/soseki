#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


from flask import (Blueprint, request, render_template)
from flask_user import roles_required

from ssk.ssk_consts import SSK_ADMIN_GROUP
from ssk.blueprints.cmd_handler import CmdHandler

bp = Blueprint('cmd', __name__, url_prefix='/cmd')


@bp.route('/terminal', methods=['GET'])
@roles_required(SSK_ADMIN_GROUP)
def terminal():
    my_page = CmdHandler.get_terminal()

    return render_template(my_page, admin_group_name=SSK_ADMIN_GROUP)


@bp.route('/cmd', methods=['POST'])
@roles_required(SSK_ADMIN_GROUP)
def cmd():
    return CmdHandler.cmd_post(request)
