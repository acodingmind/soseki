#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


from .. import db
from sqlalchemy.orm import relationship
from sqlalchemy import and_

from ..db import func_db


class Setting(func_db.Model):
    __tablename__ = 'setting'

    id = func_db.Column(func_db.Integer, primary_key=True)
    user_id = func_db.Column(func_db.Integer, func_db.ForeignKey('user.id'))
    key = func_db.Column(func_db.String(50), unique=False, nullable=False)
    type = func_db.Column(func_db.String(10), unique=False, nullable=False)
    value = func_db.Column(func_db.String(100), unique=False, nullable=False)
    system = func_db.Column('is_global', func_db.Boolean(), nullable=False, server_default='0')
    desc = func_db.Column(func_db.String(250), unique=False, nullable=True)
    updated = func_db.Column(func_db.DateTime(timezone=True), onupdate=func_db.func.current_timestamp())
    created = func_db.Column(func_db.DateTime(timezone=True), server_default=func_db.func.current_timestamp())

    owner = relationship("User", back_populates="user_settings")

    @staticmethod
    def get_by_owner_key(an_owners_id, a_key):
        my_retval = db.get_db().session.query(Setting).filter(and_(Setting.key == a_key,
                                                                   Setting.user_id == an_owners_id)).first()

        return my_retval

    @staticmethod
    def get_global_by_key(a_key):
        my_retval = db.get_db().session.query(Setting).filter(and_(Setting.key == a_key,
                                                                   Setting.system is True)).first()

        return my_retval

    @staticmethod
    def get_by_key(a_key):
        my_retval = db.get_db().session.query(Setting).filter(and_(Setting.key == a_key)).first()

        return my_retval

    def __repr__(self):
        return '<Setting %r>' % self.key
