#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


from flask import Blueprint, request

from ssk.blueprints.api_handler import ApiHandler

bp = Blueprint('api', __name__, url_prefix='/api')


@bp.route('/<string:a_version>/status/<string:a_key>', methods=['POST'])
def status(a_version, a_key):
    return ApiHandler.status(a_version, a_key)


@bp.route('/<string:a_version>/echo/<string:a_key>', methods=['POST'])
def echo(a_version, a_key):
    return ApiHandler.echo(request, a_version, a_key)

