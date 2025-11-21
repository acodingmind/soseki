#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


from ..db import func_db


class Version(func_db.Model):
    __tablename__ = 'version'

    id = func_db.Column(func_db.Integer, primary_key=True)
    ssk_version = func_db.Column(func_db.Integer, unique=False, nullable=True)
    db_version = func_db.Column(func_db.Integer, unique=False, nullable=True)

    created = func_db.Column(func_db.DateTime(timezone=True), server_default=func_db.func.current_timestamp())

    def __repr__(self):
        return '<Version %r>' % self.ssk_version
