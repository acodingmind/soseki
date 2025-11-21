#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


from sqlalchemy import desc

from ..db import func_db, get_db


class DBStats(func_db.Model):
    __tablename__ = 'db_stats'
    __bind_key__ = 'logdb'

    id = func_db.Column(func_db.Integer, primary_key=True)
    type = func_db.Column(func_db.String(10))
    table = func_db.Column(func_db.String(50))
    period = func_db.Column(func_db.String(16))
    counter = func_db.Column(func_db.Float)

    created = func_db.Column(func_db.DateTime(timezone=True), server_default=func_db.func.current_timestamp())

    def __repr__(self):
        return '<dbstats %s>' % self.path

    @staticmethod
    def get_all():
        my_ret_val = get_db().session.query(DBStats).order_by(desc(DBStats.created)).all()

        return my_ret_val

    @staticmethod
    def get_since(a_date):
        my_ret_val = get_db().session.query(DBStats).filter(DBStats.created > a_date).order_by(desc(DBStats.created)).all()

        return my_ret_val

