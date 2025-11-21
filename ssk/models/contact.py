#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


from ..db import func_db
from .. import db


class Contact(func_db.Model):
    __tablename__ = 'contact'

    id = func_db.Column(func_db.Integer, primary_key=True)
    req_id = func_db.Column(func_db.String(50), unique=False, nullable=False)
    source = func_db.Column(func_db.String(50), unique=False, nullable=False)
    name = func_db.Column(func_db.String(100), unique=False, nullable=False)
    email = func_db.Column(func_db.String(100), unique=False, nullable=False)
    details = func_db.Column(func_db.String(200), unique=False, nullable=False)
    sent = func_db.Column(func_db.Boolean, unique=False, nullable=True)

    created = func_db.Column(func_db.DateTime(timezone=True), server_default=func_db.func.current_timestamp())

    @staticmethod
    def get_by_key(a_key):
        my_ret_val = db.get_db().session.query(Contact).filter(Contact.req_id == a_key).first()

        return my_ret_val

    def __repr__(self):
        return '<Contact %r>' % self.post_id
