#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


from .. import db
from ..db import func_db
from sqlalchemy.orm import relationship, exc
from flask_user import UserMixin
from ..ssk_consts import SSK_ADMIN_GROUP


class User(func_db.Model, UserMixin):
    USER_ID = 'user.id'

    __tablename__ = 'user'

    id = func_db.Column(func_db.Integer, primary_key=True)
    username = func_db.Column(func_db.String(80), unique=True, nullable=True)

    active = func_db.Column('is_active', func_db.Boolean(), nullable=False, server_default='1')
    email = func_db.Column(func_db.String(255), nullable=True, unique=True)
    email_confirmed_at = func_db.Column('confirmed_at', func_db.DateTime())

    loggedin = func_db.Column('loggedin', func_db.Boolean(), nullable=False, server_default='0')

    password = func_db.Column(func_db.String(255), unique=False, nullable=False)
    created = func_db.Column(func_db.DateTime(timezone=True), server_default=func_db.func.current_timestamp())
    updated = func_db.Column(func_db.DateTime(timezone=True), onupdate=func_db.func.current_timestamp())
    last_login = func_db.Column(func_db.DateTime(timezone=True))
    last_access = func_db.Column(func_db.DateTime(timezone=True))
    num_of_logins = func_db.Column(func_db.Integer, nullable=False, server_default='0')

    first_name = func_db.Column(func_db.String(50), nullable=True)
    last_name = func_db.Column(func_db.String(50), nullable=True)

    roles = relationship('Role', secondary='user_roles', back_populates="users")
    #version 8
    subs = relationship('Subs', secondary='user_subs', back_populates="users")

    jobs = relationship("Job", back_populates="executor")
    user_settings = relationship("Setting", back_populates="owner")
    api_keys = relationship("ApiKey", back_populates="owner")

    def __repr__(self):
        return self.email

    def has_role(self, a_role):
        my_role_names = (myTmpRole.name for myTmpRole in self.roles)

        return a_role in my_role_names

    def is_admin(self):
        my_role_names = (myTmpRole.name for myTmpRole in self.roles)

        return SSK_ADMIN_GROUP in my_role_names

    @staticmethod
    def all_roles_str(an_inid):
        my_user = db.get_db().session.query(User).filter(User.inid == an_inid).first()
        my_ret_val = (myTmpRole.name for myTmpRole in my_user.roles)

        return ", ".join(my_ret_val)

    @staticmethod
    def get_by_inid(an_inid):
        my_ret_val = db.get_db().session.query(User).filter(User.inid == an_inid).first()

        return my_ret_val

    @staticmethod
    def get_by_id(an_id):
        my_ret_val = db.get_db().session.query(User).filter(User.id == an_id).first()

        return my_ret_val

    @staticmethod
    def get_by_email(an_email):
        my_ret_val = db.get_db().session.query(User).filter(User.email == an_email).first()

        return my_ret_val

    @staticmethod
    def get_by_name(a_name):
        my_ret_val = None
        try:
            my_ret_val = db.get_db().session.query(User).filter(User.username == a_name).one()
        except exc.NoResultFound:
            print("User {} not found".format(a_name))

        return my_ret_val


class Role(func_db.Model):
    ROLE_ID = "role.id"
    __tablename__ = 'role'

    id = func_db.Column(func_db.Integer(), primary_key=True)
    name = func_db.Column(func_db.String(50), unique=True)

    active = func_db.Column('is_active', func_db.Boolean(), nullable=True, server_default='1')

    users = relationship('User', secondary='user_roles', back_populates="roles")

    created = func_db.Column(func_db.DateTime(timezone=True), server_default=func_db.func.now())
    updated = func_db.Column(func_db.DateTime(timezone=True), onupdate=func_db.func.now())

    @staticmethod
    def get_by_name(a_name):
        return db.get_db().session.query(Role).filter(Role.name == a_name).first()

class UserRoles(func_db.Model):
    __tablename__ = 'user_roles'

    user_id = func_db.Column(func_db.Integer(), func_db.ForeignKey(User.USER_ID), primary_key=True)
    role_id = func_db.Column(func_db.Integer(), func_db.ForeignKey(Role.ROLE_ID), primary_key=True)

    created = func_db.Column(func_db.DateTime(timezone=True), server_default=func_db.func.now())
    updated = func_db.Column(func_db.DateTime(timezone=True), onupdate=func_db.func.now())


class UserInvitation(func_db.Model):
    __tablename__ = 'user_invitations'
    id = func_db.Column(func_db.Integer, primary_key=True)
    email = func_db.Column(func_db.String(255), nullable=False)
    invited_by_user_id = func_db.Column(func_db.Integer, func_db.ForeignKey(User.USER_ID))

#version 8
class Transaction(func_db.Model):
    __tablename__ = 'user_transaction'
    id = func_db.Column(func_db.Integer, primary_key=True)
    description = func_db.Column(func_db.String(255), nullable=False)
    invited_by_user_id = func_db.Column(func_db.Integer, func_db.ForeignKey(User.USER_ID))


class Subs(func_db.Model):
    SUBS_ID = "subs.id"
    __tablename__ = 'subs'

    id = func_db.Column(func_db.Integer(), primary_key=True)
    name = func_db.Column(func_db.String(50), unique=True)

    active = func_db.Column('is_active', func_db.Boolean(), nullable=True, server_default='1')
    price = func_db.Column(func_db.Float())

    users = relationship('User', secondary='user_subs', back_populates="subs")

    created = func_db.Column(func_db.DateTime(timezone=True), server_default=func_db.func.now())
    updated = func_db.Column(func_db.DateTime(timezone=True), onupdate=func_db.func.now())

    @staticmethod
    def get_by_name(a_name):
        return db.get_db().session.query(Subs).filter(Subs.name == a_name).first()


class UserSubs(func_db.Model):
    __tablename__ = 'user_subs'

    user_id = func_db.Column(func_db.Integer(), func_db.ForeignKey(User.USER_ID), primary_key=True)
    subs_id = func_db.Column(func_db.Integer(), func_db.ForeignKey(Subs.SUBS_ID), primary_key=True)

    expiration = func_db.Column(func_db.DateTime(timezone=True), server_default=func_db.func.now())
    created = func_db.Column(func_db.DateTime(timezone=True), server_default=func_db.func.now())
    updated = func_db.Column(func_db.DateTime(timezone=True), onupdate=func_db.func.now())
