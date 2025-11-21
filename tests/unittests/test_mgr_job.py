#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#

from flask import current_app

from ssk import SSK_ADMIN_GROUP, CmdProcessor
from ssk.globals.job_mgr import JobMgr
from ssk.logic.jobs.empty_job import EmptyJob
from ssk.logic.jobs.page_stat_job import PageStatJob
from ssk.logic.jobs.health_check_job import HealthCheckJob
from unittest import mock


def test_job_cnt(app):
    with app.app_context():
        my_blog_mgr = JobMgr()

        assert my_blog_mgr.total_active() == 0
        assert my_blog_mgr.total_queued() == 0


@mock.patch('flask_login.utils._get_user')
def run_queue_job(current_user):
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
                       a_max_collectors=0) # to make sure next job is queued

    my_task = EmptyJob(current_app, a_args=['name'])
    CmdProcessor.submit_cmd(my_task)

    assert my_job_mgr.total_queued() == 1
    assert my_job_mgr.is_queued(my_task.get_task_id())

    my_job_mgr.stop_job(my_task.get_task_id())
    assert my_job_mgr.total_queued() == 0
    assert not my_job_mgr.is_queued(my_task.get_task_id())

    my_job_mgr.delete_job(my_task.get_task_id())

    CmdProcessor.stop()


@mock.patch('flask_login.utils._get_user')
def run_empty(current_user):
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
                       a_max_collectors=5)

    import time
    time.sleep(3)

    my_task = EmptyJob(current_app, a_args=['name'])
    CmdProcessor.submit_cmd(my_task)

    time.sleep(1)
    assert my_job_mgr.total_active() == 1
    assert my_job_mgr.is_active(my_task.get_task_id())

    my_job_mgr.stop_job(my_task.get_task_id())
    assert my_job_mgr.total_active() == 0
    assert not my_job_mgr.is_active(my_task.get_task_id())

    my_job_mgr.delete_job(my_task.get_task_id())

    CmdProcessor.stop()


# def test_empty_job_startstop(app):
#     with app.app_context():
#         run_empty()


def test_page_stat_job_startstop(app):
    with app.app_context():
        my_page_stat = PageStatJob(current_app, a_args=["stats"])
        my_page_stat.work()


def test_health_check_job_startstop(app):
    with app.app_context():
        my_health = HealthCheckJob(current_app, a_args=["health"])
        my_health.work()


def test_job_queuestop(app):
    with app.app_context():
        run_queue_job()
