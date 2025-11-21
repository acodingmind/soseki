#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


from sqlalchemy.orm import relationship

from .. import db
from ..db import func_db


class ApiKey(func_db.Model):
    __tablename__ = 'apikey'

    id = func_db.Column(func_db.Integer, primary_key=True)
    user_id = func_db.Column(func_db.Integer, func_db.ForeignKey('user.id'))
    active = func_db.Column('is_active', func_db.Boolean(), nullable=False, server_default='1')
    key = func_db.Column(func_db.String(50), unique=True, nullable=False)

    updated = func_db.Column(func_db.DateTime(timezone=True), onupdate=func_db.func.current_timestamp())
    created = func_db.Column(func_db.DateTime(timezone=True), server_default=func_db.func.current_timestamp())

    owner = relationship("User", back_populates="api_keys")

    @staticmethod
    def get_all_active():
        my_ret_val = db.get_db().session.query(ApiKey).filter(ApiKey.active == 1).all()

        return my_ret_val

    @staticmethod
    def get_by_key(a_key):
        my_ret_val = db.get_db().session.query(ApiKey).filter(ApiKey.key == a_key).first()

        return my_ret_val

    @staticmethod
    def get_by_user(a_user_id):
        my_ret_val = db.get_db().session.query(ApiKey).filter(ApiKey.user_id == a_user_id).all()

        return my_ret_val

    def __repr__(self):
        return '<ApiKey %r>' % self.id
