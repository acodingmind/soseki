#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


from flask import g, current_app


def get_logic():
    if 'logic' not in g:
        g.logic = current_app.bus_logic.get_instance()

    return g.logic
