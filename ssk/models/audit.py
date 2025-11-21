#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


from ..db import func_db


class Audit(func_db.Model):
    __tablename__ = 'audit'

    id = func_db.Column(func_db.Integer, primary_key=True)
    by_user = func_db.Column(func_db.String(255), unique=False, nullable=True)
    category = func_db.Column(func_db.String(10), unique=False, nullable=True)
    description = func_db.Column(func_db.String(250), unique=False, nullable=False)
    status = func_db.Column(func_db.String(10), unique=False, nullable=True)
    created = func_db.Column(func_db.DateTime(timezone=True), server_default=func_db.func.current_timestamp())

    def __repr__(self):
        return '<Audit %r>' % self.description
