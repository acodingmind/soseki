#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#

import pytest
from flask import Flask, current_app

import ssk as sut
from ssk.logic.bus_logic import BusLogic
from ssk.db import db_clean, get_version, set_version, db_create


class DbUpgrader:
    @staticmethod
    def ver1():
        my_version = 1
        current_app.logger.info("upgrading to {}".format(my_version))

        my_db_version = get_version()

        if my_db_version.db_version < my_version:
            set_version(my_version)

    @staticmethod
    def get_upgrade_functions():
        my_retval = [DbUpgrader.ver1]

        return my_retval


@pytest.fixture()
def app():
    my_app = Flask(__name__, instance_relative_config=True)
    my_app = sut.init_ssk(my_app, BusLogic, DbUpgrader, True)

    with my_app.app_context():
        db_clean()
        db_create()

    sut.start_ssk(my_app, True)

    yield my_app

    with my_app.app_context():
        db_clean()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def current_user(app):
    return current_user
