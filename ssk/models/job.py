#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


from sqlalchemy.orm import relationship

from ..db import func_db, get_db


class Job(func_db.Model):
    __tablename__ = 'job'

    id = func_db.Column(func_db.Integer, primary_key=True)
    task_id = func_db.Column(func_db.String(50), unique=False, nullable=False)
    name = func_db.Column(func_db.String(25), unique=False, nullable=False)
    action = func_db.Column(func_db.String(50), unique=False, nullable=False)
    status = func_db.Column(func_db.String(50), unique=False, nullable=False)
    logfile = func_db.Column(func_db.String(50), unique=False, nullable=True)
    progress = func_db.Column(func_db.Integer)

    user_id = func_db.Column(func_db.Integer(), func_db.ForeignKey('user.id', ondelete='CASCADE'))
    executor = relationship("User", back_populates="jobs")

    created = func_db.Column(func_db.DateTime(timezone=True), server_default=func_db.func.current_timestamp())
    started = func_db.Column(func_db.DateTime(timezone=True))
    done = func_db.Column(func_db.DateTime(timezone=True))

    @staticmethod
    def get_by_key(a_key):
        my_ret_val = get_db().session.query(Job).filter(Job.task_id == a_key).first()

        return my_ret_val

    def __repr__(self):
        return '<Job %r>' % self.task_id
