#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#

from flask import current_app

from ssk.globals.api_gate import ApiGate


def test_set_open():
    my_api_gate = ApiGate()

    assert not my_api_gate.is_open()
    my_api_gate.set_open(True)
    assert my_api_gate.is_open()
    my_api_gate.set_open(False)
    assert not my_api_gate.is_open()


def test_get_new_key(app):
    with app.app_context():
        my_api_gate = ApiGate()

        my_zero_user = current_app.config["USER_FREE_EMAIL"]
        assert my_api_gate.add_api_key(my_zero_user) is not None


def test_apigate(app):
    with app.app_context():
        my_api_gate = ApiGate()
        my_api_gate.init()
        my_api_gate.load()

        my_new_key = my_api_gate.get_new_key()

        assert not my_api_gate.is_open()
        assert my_api_gate.num_total_keys() == 1
        assert my_api_gate.num_active_keys() == 0
        assert len(my_api_gate.active_now()) == 0
        assert not my_api_gate.is_active_now(my_new_key)


