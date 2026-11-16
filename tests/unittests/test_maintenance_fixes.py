#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#

from datetime import timedelta
from unittest.mock import Mock, patch

import pytest
from flask import current_app
from sqlalchemy import inspect, text

from ssk.db import get_db, get_version
from ssk.utils import now


def _job(a_class, a_args):
    my_job = a_class(current_app, a_args=a_args)
    my_job.logs = []
    my_job.audits = []
    my_job.write_to_log = my_job.logs.append
    my_job.write_to_audit = lambda a_status, a_mesg: my_job.audits.append((a_status, a_mesg))
    return my_job


def _columns(an_engine, a_table):
    return [my_col["name"] for my_col in inspect(an_engine).get_columns(a_table)]


def _set_ssk_version(a_version):
    my_current = get_version()
    with get_db().engine.begin() as my_conn:
        my_conn.execute(text("insert into version (db_version, ssk_version) values (:d, :s)"),
                        {"d": my_current.db_version, "s": a_version})


def test_fresh_db_has_single_sched_on_setting(app):
    with app.app_context():
        from ssk.models.setting import Setting
        assert Setting.query.filter_by(key="SCHED_ON").count() == 1


def test_mail_command_alias(app):
    with app.app_context():
        from ssk.logic.cmd.admin_cmd import AdminCmd
        from ssk.logic.cmd.mail_cmd import MailCmd
        assert isinstance(AdminCmd().get_cmd("mail"), MailCmd)
        assert isinstance(AdminCmd().get_cmd("m"), MailCmd)


@pytest.mark.parametrize("a_table, a_model_path", [
    ("audit", "ssk.models.audit.Audit"),
    ("logdb.access", "ssk.models.access.Access"),
])
def test_db_cleanup_deletes_only_old_rows(app, a_table, a_model_path):
    from importlib import import_module
    from ssk.logic.jobs.db_cleanup_job import DbCleanupJob

    my_module, my_class = a_model_path.rsplit(".", 1)
    my_model = getattr(import_module(my_module), my_class)

    with app.test_request_context():
        my_session = get_db().session
        for my_age_days, my_tag in ((30, "old"), (1, "new")):
            my_row = my_model()
            if my_class == "Audit":
                my_row.category, my_row.by_user, my_row.status, my_row.description = "T", "t", "OK", my_tag
            else:
                my_row.remote_addr, my_row.method, my_row.protocol, my_row.response = "1.1.1.1", "GET", "http", "200"
                my_row.path, my_row.user, my_row.response_time = "/" + my_tag, "", 1
            my_row.created = now() - timedelta(days=my_age_days)
            my_session.add(my_row)
        my_session.commit()
        my_before = my_model.query.count()

        my_job = _job(DbCleanupJob, ["dbcleanup {}".format(a_table), a_table, 21])
        my_job.work()

        my_session.expire_all()
        assert my_job.audits and my_job.audits[0][0] == "OK", my_job.logs
        assert my_model.query.count() < my_before
        assert my_model.query.filter(my_model.created < now() - timedelta(days=21)).count() == 0
        assert my_model.query.filter(my_model.created >= now() - timedelta(days=2)).count() >= 1


def test_db_cleanup_rejects_unknown_table(app):
    from ssk.logic.jobs.db_cleanup_job import DbCleanupJob

    with app.test_request_context():
        my_job = _job(DbCleanupJob, ["dbcleanup x", "audit; drop table user", 21])
        my_job.work()

        assert my_job.audits[0][0] == "NOK"
        assert "user" in inspect(get_db().engine).get_table_names()


def test_upgrades_2_to_4_add_missing_columns(app):
    from ssk.ssk_upgrader import SSKUpgrader

    with app.app_context():
        SSKUpgrader._to_skip.clear()
        my_engine = get_db().engine
        with my_engine.begin() as my_conn:
            my_conn.execute(text("CREATE TABLE notes (id INTEGER PRIMARY KEY)"))
        try:
            for my_version in (2, 3, 4):
                _set_ssk_version(my_version - 1)
                getattr(SSKUpgrader, "ver{}".format(my_version))()
                assert get_version().ssk_version == my_version

            assert {"summary", "category", "meta"} <= set(_columns(my_engine, "notes"))
            assert "response_time" in _columns(get_db().engines["logdb"], "access")

            # running again must not fail on the existing columns
            _set_ssk_version(2)
            SSKUpgrader.ver3()
            SSKUpgrader.ver4()
        finally:
            with my_engine.begin() as my_conn:
                my_conn.execute(text("DROP TABLE IF EXISTS notes"))


def test_upgrades_3_and_4_skip_missing_notes_table(app):
    from ssk.ssk_upgrader import SSKUpgrader

    with app.app_context():
        SSKUpgrader._to_skip.clear()
        _set_ssk_version(2)
        SSKUpgrader.ver3()
        SSKUpgrader.ver4()
        assert get_version().ssk_version == 4


def test_health_check_skips_url_when_root_url_empty(app):
    from ssk.logic.jobs.health_check_job import HealthCheckJob

    with app.test_request_context():
        current_app.config["ROOT_URL"] = ""
        with patch("ssk.logic.jobs.health_check_job.requests.get") as my_get:
            _job(HealthCheckJob, ["health"]).work()
        my_get.assert_not_called()


def test_health_check_request_has_timeout(app):
    from ssk.logic.jobs.health_check_job import HealthCheckJob, HEALTH_CHECK_TIMEOUT

    with app.test_request_context():
        current_app.config["ROOT_URL"] = "https://example.invalid"
        with patch("ssk.logic.jobs.health_check_job.requests.get",
                   return_value=Mock(status_code=200)) as my_get:
            _job(HealthCheckJob, ["health"]).work()
        my_get.assert_called_once_with("https://example.invalid", timeout=HEALTH_CHECK_TIMEOUT)


def test_template_configs_do_not_call_external_site():
    import yaml
    for my_profile in ("app/cfg/lite.yaml", "app/cfg/tst.yaml"):
        with open(my_profile) as my_file:
            assert yaml.safe_load(my_file)["ssk"]["ROOT_URL"]["string"] == ""


def _make_pre_ver8_db():
    """Remove what upgrade 8 adds, so the test database looks like one created before it."""
    my_pro_email = current_app.config["USER_PRO_EMAIL"]
    with get_db().engine.begin() as my_conn:
        my_conn.execute(text("delete from user_subs"))
        my_conn.execute(text("delete from subs"))
        my_conn.execute(text("delete from user_roles where user_id = (select id from user where email = :e)"),
                        {"e": my_pro_email})
        my_conn.execute(text("delete from user where email = :e"), {"e": my_pro_email})
    get_db().session.expire_all()
    _set_ssk_version(7)


def test_upgrade_8_on_pre_ver8_db(app):
    from ssk.models.user import Subs, User
    from ssk.ssk_upgrader import SSKUpgrader

    with app.app_context():
        SSKUpgrader._to_skip.clear()
        _make_pre_ver8_db()

        SSKUpgrader.ver8()
        # running it again must not duplicate users or memberships
        _set_ssk_version(7)
        SSKUpgrader.ver8()

        assert get_version().ssk_version == 8

        my_config = current_app.config
        my_pro_user = User.get_by_email(my_config["USER_PRO_EMAIL"])
        assert my_pro_user is not None
        assert current_app.user_manager.verify_password(my_config["USER_PRO_PASS"], my_pro_user.password)
        assert my_config["USER_GROUP_NAME"] in [my_role.name for my_role in my_pro_user.roles]

        my_members = {my_subs.name: sorted(my_user.email for my_user in my_subs.users)
                      for my_subs in Subs.query.all()}
        assert my_members == {
            my_config["FREE_SUB"]: [my_config["USER_FREE_EMAIL"]],
            my_config["PRO_SUB"]: sorted([my_config["USER_PRO_EMAIL"], my_config["ADMIN_EMAIL"]]),
        }


@pytest.mark.parametrize("a_kit_id", ["", "abc123kit"])
def test_error_page_uses_configured_font_awesome(a_kit_id):
    import jinja2
    my_env = jinja2.Environment(loader=jinja2.FileSystemLoader("ssk/templates"))
    my_html = my_env.get_template("500.html").render(config={"FONTAWESOME_KIT_ID": a_kit_id},
                                                      user_manager=Mock(USER_APP_NAME="App"), error_id="x")

    assert "183ab5233b" not in my_html
    if a_kit_id:
        assert "kit.fontawesome.com/abc123kit.js" in my_html
    else:
        assert "kit.fontawesome.com" not in my_html
        assert "font-awesome/6.5.1/css/all.min.css" in my_html


def test_layouts_have_no_dead_cdn_scripts():
    for my_path in ("app/html/local/layout.html", "ssk/templates/local/layout.html"):
        with open(my_path) as my_file:
            assert "oss.maxcdn.com" not in my_file.read()
