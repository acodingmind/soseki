#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


from ..db import func_db, get_db


class Access(func_db.Model):
    __tablename__ = 'access'
    __bind_key__ = 'logdb'

    id = func_db.Column(func_db.Integer, primary_key=True)
    remote_addr = func_db.Column(func_db.String(100))
    method = func_db.Column(func_db.String(100))
    protocol = func_db.Column(func_db.String(100))
    path = func_db.Column(func_db.String(250))
    response = func_db.Column(func_db.String(100))
    response_time = func_db.Column(func_db.Integer)
    user = func_db.Column(func_db.String(100))

    created = func_db.Column(func_db.DateTime(timezone=True), server_default=func_db.func.current_timestamp())

    def __repr__(self):
        return '<access %s>' % self.path

    @staticmethod
    def get_by_key(a_key):
        my_ret_val = get_db().session.query(Access).filter(Access.req_key == a_key).first()

        return my_ret_val
