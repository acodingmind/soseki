#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


from sqlalchemy import and_, desc

from ..db import func_db, get_db


class Stats(func_db.Model):
    __tablename__ = 'stats'
    __bind_key__ = 'logdb'

    id = func_db.Column(func_db.Integer, primary_key=True)
    day = func_db.Column(func_db.String(16))
    path = func_db.Column(func_db.String(10))
    hits = func_db.Column(func_db.Integer)
    mean_response_time = func_db.Column(func_db.Float)
    max_response_time = func_db.Column(func_db.Integer)
    last_processed = func_db.Column(func_db.Integer)

    created = func_db.Column(func_db.DateTime(timezone=True), server_default=func_db.func.current_timestamp())

    def __repr__(self):
        return '<stats %s>' % self.path

    @staticmethod
    def get_last_processed_id():
        my_ret_val = 0
        my_stats_db = get_db().session.query(Stats).order_by(desc(Stats.created)).first()
        if my_stats_db is not None:
            my_ret_val = my_stats_db.last_processed

        return my_ret_val

    @staticmethod
    def get_all():
        my_ret_val = get_db().session.query(Stats).order_by(desc(Stats.created)).all()

        return my_ret_val

    @staticmethod
    def get_last(a_days):
        my_ret_val = get_db().session.query(Stats).order_by(desc(Stats.created)).limit(a_days)

        return my_ret_val

    @staticmethod
    def get_since(a_date):
        my_ret_val = get_db().session.query(Stats).filter(Stats.created > a_date).order_by(desc(Stats.created)).all()

        return my_ret_val

    @staticmethod
    def get_by_date(a_day, a_page):
        my_ret_val = get_db().session.query(Stats).filter(and_(Stats.day == a_day, Stats.path == a_page)).first()

        return my_ret_val
