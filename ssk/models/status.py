#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


from ..db import func_db


class Status(func_db.Model):
    __tablename__ = 'status'
    __bind_key__ = 'logdb'

    id = func_db.Column(func_db.Integer, primary_key=True)
    api_status = func_db.Column(func_db.String(100))
    api_now_threshold = func_db.Column(func_db.String(100))
    api_active_now = func_db.Column(func_db.Integer)
    api_max_active = func_db.Column(func_db.Integer)
    api_total = func_db.Column(func_db.Integer)
    users = func_db.Column(func_db.Integer)
    users_active = func_db.Column(func_db.Integer)
    conf_keys = func_db.Column(func_db.Integer)
    audit_cnt = func_db.Column(func_db.Integer)
    response_time = func_db.Column(func_db.Integer)
    mem = func_db.Column(func_db.Float)

    created = func_db.Column(func_db.DateTime(timezone=True), server_default=func_db.func.current_timestamp())

    def __repr__(self):
        return '<Status %r>' % self.id
