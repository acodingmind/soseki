#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


from flask import current_app
from flask_login import current_user
import uuid
import json
from ssk.lg import get_logic


class CmdHandler(object):
    PAGE_TERMINAL = 'ssk/admin/terminal.html'

    @staticmethod
    def get_terminal():
        return CmdHandler.PAGE_TERMINAL

    @staticmethod
    def cmd_post(a_request):
        my_request_json = a_request.json
        my_root_cmd = get_logic().get_root_cmd()
        try:
            my_params = [my_request_json["method"]]
            my_params.extend(my_request_json["params"])

            if current_user.is_admin():
                _, my_mesg = my_root_cmd.exec(my_params)
            else:
                my_mesg = "Access Denied"
        except Exception as an_e:
            my_error_id = str(uuid.uuid4())
            current_app.logger.error("{} {}".format(my_error_id, an_e))
            my_mesg = '[[ print "sorry, there was a problem, we will look into it asap.\nIt has been logged under: {}\n"]]'.format(
                my_error_id)

        my_response = {"jsonrpc": "2.0", "result": my_mesg, "id": 3}

        return json.dumps(my_response)
