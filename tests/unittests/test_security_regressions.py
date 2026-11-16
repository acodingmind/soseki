#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#

import os
from datetime import datetime
from unittest.mock import patch

import pytest
from flask import current_app

from ssk.db import get_db
from ssk.globals.api_gate import ApiGate
from ssk.models.apikey import ApiKey
from ssk.models.job import Job
from ssk.models.user import User


@pytest.fixture(autouse=True)
def mock_error_templates():
    # error handlers render templates that are not on the test app's template path
    with patch('ssk.render_template', side_effect=lambda t, *a, **k: t), \
         patch('ssk.blueprints.home.render_template', side_effect=lambda t, *a, **k: t):
        yield


def _login(client, a_email):
    my_user = User.get_by_email(a_email)
    with client.session_transaction() as my_session:
        my_session["_user_id"] = my_user.get_id()
        my_session["_fresh"] = True


@pytest.fixture()
def victim_job(app, tmp_path):
    """A finished job owned by the 'pro' user, with a log file on disk."""
    my_log = tmp_path / "victim.log"
    my_log.write_text("secret job output")

    with app.app_context():
        my_owner = User.get_by_email(current_app.config["USER_PRO_EMAIL"])
        my_job = Job(task_id="victim-tid", name="victim", action="x", status="DONE",
                     logfile=str(my_log), progress=100, started=datetime.now(), user_id=my_owner.id)
        get_db().session.add(my_job)
        get_db().session.commit()

    return str(my_log)


def _job_exists(app):
    with app.app_context():
        return Job.get_by_key("victim-tid") is not None


@pytest.mark.parametrize("a_who", [None, "USER_FREE_EMAIL"])
def test_task_endpoints_reject_non_owner(app, client, victim_job, a_who):
    if a_who is not None:
        with app.app_context():
            _login(client, current_app.config[a_who])

    # ssk's request_error handler reports every 4xx as 400
    assert client.get("/ssk/task_log_download/victim-tid").status_code == 400
    assert client.get("/ssk/progress/victim-tid").status_code == 400

    my_response = client.post("/ssk/tasks_action", data={"delete": "victim-tid"})
    assert my_response.status_code in (200, 400)
    assert _job_exists(app)
    assert os.path.exists(victim_job)


def test_task_endpoints_allow_owner(app, client, victim_job):
    with app.app_context():
        _login(client, current_app.config["USER_PRO_EMAIL"])

    my_response = client.get("/ssk/task_log_download/victim-tid")
    assert my_response.status_code == 200
    assert my_response.data == b"secret job output"
    assert client.get("/ssk/progress/victim-tid").status_code == 200


@pytest.fixture()
def api_key(app):
    with app.app_context():
        my_key = ApiKey.query.filter_by(active=True).first().key
    ApiGate.set_open(True)
    yield my_key
    ApiGate.set_open(False)


def _echo(client, a_key):
    return client.post("/api/v1/echo/{}".format(a_key), json={"echo": "hi"})


def test_revoked_api_key_stops_working_immediately(app, client, api_key):
    assert _echo(client, api_key).status_code == 200

    with app.app_context():
        my_key = ApiKey.query.filter_by(key=api_key).first()
        my_key.active = False
        get_db().session.commit()
        ApiGate.load()

    assert _echo(client, api_key).status_code == 400


def test_closed_api_rejects_active_session(app, client, api_key):
    assert _echo(client, api_key).status_code == 200

    ApiGate.set_open(False)

    assert _echo(client, api_key).status_code == 400
    # status keeps working while the api is closed, by design
    assert client.post("/api/v1/status/{}".format(api_key)).status_code == 200
