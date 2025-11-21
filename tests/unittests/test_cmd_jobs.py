#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#

from flask import current_app

from ssk import SSK_ADMIN_GROUP, CmdProcessor
from ssk.globals.job_mgr import JobMgr
from ssk.logic.cmd.job_cmd import JobCmd

from unittest import mock


@mock.patch('flask_login.utils._get_user')
def run(current_user):
    attrs = {
        'id': 1,
        'email': 'admin@soseki.io',
        'name': 'Soseki Admin',
        'roles': [SSK_ADMIN_GROUP]
    }
    current_user.return_value = mock.Mock(is_authenticated=True,
                                          is_anonymous=False, **attrs)
    current_user.return_value.is_admin.return_value = True

    my_job_mgr = JobMgr()
    CmdProcessor.start(a_job_mgr=my_job_mgr,
                       a_logger=current_app.logger,
                       a_max_collectors=5) # to make sure next job is NOT queued

    my_cmd = JobCmd()
    my_params = ["l"]
    my_ok, my_res = my_cmd.exec(my_params)
    assert my_ok

    my_params = ["r", "aa"]
    my_job_id, my_mesg = my_cmd.exec(my_params)
    assert my_job_id is not None

    my_params = ["l"]
    my_ok, my_res = my_cmd.exec(my_params)
    assert my_ok
    assert (my_job_id in my_res)

    my_params = ["d", my_job_id]
    my_res, my_mesg = my_cmd.exec(my_params)
    assert not my_res

    my_params = ["k", my_job_id]
    my_res, my_mesg = my_cmd.exec(my_params)
    assert my_res

    my_params = ["d", my_job_id]
    my_res, my_mesg = my_cmd.exec(my_params)
    assert my_res

    my_params = ["l"]
    my_ok, my_res = my_cmd.exec(my_params)
    assert my_ok
    assert (my_job_id not in my_res)

    CmdProcessor.stop()

# ToDo fix it
# def test_job_cmd(app):
#     with app.app_context():
#         run()




