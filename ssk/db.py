#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


import uuid

from flask_sqlalchemy import SQLAlchemy
from flask import current_app, g
from datetime import datetime

from sqlalchemy_utils import database_exists, create_database
from ssk.globals.setting_parser import SettingParser

func_db = SQLAlchemy()


def truncate_password(password):
    """Truncate password to 72 bytes for bcrypt compatibility.
    
    Bcrypt has a 72-byte limit. This function truncates passwords to 72 bytes
    to avoid ValueError: password cannot be longer than 72 bytes.
    
    Version: 2025-01-12T14:42:00Z
    """
    if isinstance(password, str):
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            return password_bytes[:72].decode('utf-8', errors='ignore')
    return password


def get_db():
    if 'db' not in g:
        g.db = func_db

    return g.db


def db_version_check():
    from .models.audit import Audit
    current_app.logger.info("DB Version Check {}".format(current_app.config["DB_HOST"]))

    if not database_exists(current_app.config["SQLALCHEMY_DATABASE_URI"]):
        current_app.logger.info("Func Database Does Not Exist")

        current_app.logger.info("Creating Func DB")
        create_database(current_app.config["SQLALCHEMY_DATABASE_URI"])

        current_app.logger.info("Creating Log DB")
        create_database(current_app.config["SQLALCHEMY_BINDS"]['logdb'])

        current_app.logger.info("Creating Tables")
        db_create()
        db_init()
        current_app.logger.info("Database {} Created".format(current_app.config["DB_HOST"]))
    else:
        current_app.logger.info("Database Exists")

    my_req_db_ver = int(current_app.config["DB_MODEL_VERSION"])
    my_req_ssk_ver = int(current_app.config["SSK_DB_MODEL_VERSION"])

    my_db_version = None
    try:
        my_db_version = get_version()
    except Exception as a_problem:
        current_app.logger.info("DB Schema still Does Not Exist {}".format(a_problem))

    if my_db_version is None:
        current_app.logger.info("DB Version Not Found")
        current_app.logger.info("Creating Tables")
        db_clean()
        db_create()
        db_init()
        current_app.logger.info("Database {} Created".format(current_app.config["DB_HOST"]))

        my_db_version = get_version()

    current_app.logger.info("DB Ver:{} vs {} SSK DB Ver {} vs {}".format(my_db_version.db_version,
                                                                         my_req_db_ver,
                                                                         my_db_version.ssk_version,
                                                                         my_req_ssk_ver))

    my_stop = False
    if my_db_version.ssk_version < my_req_ssk_ver:
        current_app.logger.info("SSK DB {} < {}".format(my_db_version.ssk_version,
                                                        my_req_ssk_ver))
        upgrade_ssk_db(my_db_version.ssk_version, my_req_ssk_ver)

        my_desc = "SSK DB {} < {}: Upgrade".format(my_db_version.ssk_version, my_req_ssk_ver)
    elif my_db_version.ssk_version > my_req_ssk_ver:
        my_stop = True
        current_app.logger.error("SSK DB Version is ahead of Required Version")
        my_desc = "SSK DB {} > {}: Stop".format(my_db_version.ssk_version, my_req_ssk_ver)
    else:
        current_app.logger.info("SSK DB {} == {}".format(my_db_version.ssk_version,
                                                         my_req_ssk_ver))

        my_desc = "SSK DB {} == {}: No Action Needed".format(my_db_version.ssk_version,
                                                             my_req_ssk_ver)

    if not my_stop:
        if my_db_version.db_version < my_req_db_ver:
            current_app.logger.info("IMP DB {} < {} Upgrading".format(my_db_version.db_version,
                                                                      my_req_db_ver))

            upgrade_imp_db(my_db_version.db_version, my_req_db_ver)
            my_desc = "IMP DB {} < {}: Upgrade".format(my_db_version.db_version,
                                                       my_req_db_ver)

        elif my_db_version.db_version > my_req_db_ver:
            my_stop = True
            current_app.logger.error("IMP DB Version is ahead of Required Version")
            my_desc = "IMP DB {} > {}: Stop".format(my_db_version.db_version,
                                                    my_req_db_ver)
        else:
            current_app.logger.info("IMP DB no upgrade needed")
            my_desc = "IMP DB {} == {}: No Action".format(my_db_version.db_version,
                                                          my_req_db_ver)

    my_audit = Audit()
    my_audit.by_user = "SYSTEM"
    my_audit.category = "START"
    my_audit.description = my_desc
    if my_stop:
        my_audit.status = "NOK"
    else:
        my_audit.status = "OK"
    get_db().session.add(my_audit)
    get_db().session.commit()

    if my_stop:
        raise (SystemExit())


def get_version():
    from .models.version import Version

    return get_db().session.query(Version).order_by(Version.id.desc()).first()


def set_version(a_version):
    from sqlalchemy import text
    from .models.version import Version

    my_db_version = get_db().session.query(Version).order_by(Version.id.desc()).first()
    if my_db_version.db_version < a_version:
        my_sql = 'insert into version (db_version, ssk_version) values({}, {})'.format(a_version,
                                                                                       my_db_version.ssk_version)
        with get_db().engine.connect() as my_connection:
            my_connection.execute(text(my_sql))
            my_connection.commit()


def set_ssk_version(a_version):
    from sqlalchemy import text
    from .models.version import Version

    my_db_version = get_db().session.query(Version).order_by(Version.id.desc()).first()
    if my_db_version.ssk_version < a_version:
        my_sql = 'insert into version (db_version, ssk_version) values({}, {})'.format(my_db_version.db_version,
                                                                                       a_version)
        with get_db().engine.connect() as my_connection:
            my_connection.execute(text(my_sql))
            my_connection.commit()


def upgrade_imp_db(a_from, a_to):
    my_functions = current_app.db_upgrader.get_upgrade_functions()

    for my_tmp_ver in range(a_from, a_to + 1):
        current_app.logger.info("Upgrading IMP DB to {}".format(my_tmp_ver + 1))

        try:
            my_idx = my_tmp_ver-1
            if my_idx >= 0:
                my_functions[my_idx]()
        except Exception as an_e:
            current_app.logger.error("IMP DB Upgrade failed {}".format(str(an_e)))


def upgrade_ssk_db(a_from, a_to):
    from ssk.ssk_upgrader import SSKUpgrader
    my_functions = SSKUpgrader().get_upgrade_functions()

    for my_tmp_ver in range(a_from, a_to + 1):
        current_app.logger.info("Upgrading SSK DB to {}".format(my_tmp_ver + 1))

        try:
            my_idx = my_tmp_ver-1
            if my_idx >= 0:
                my_functions[my_idx]()
        except Exception as an_e:
            current_app.logger.error("SSK DB Upgrade failed {}".format(str(an_e)))


def close_db(e=None):
    current_app.logger.info("Closing Func DB {} e: {}".format(current_app.config["DB_HOST"], e))
    my_db = g.pop('db', None)

    if my_db is not None:
        my_db.session.remove()


def close_logdb(e=None):
    current_app.logger.info("Closing Log DB {} e: {}".format(current_app.config["DB_HOST"], e))
    my_db = g.pop('logdb', None)

    if my_db is not None:
        my_db.session.remove()


# noinspection PyUnresolvedReferences
def db_clean():
    current_app.logger.info("db clean {}".format(current_app.config["DB_HOST"]))

    func_db.session.remove()

    from .models.audit import Audit
    from .models.user import User
    from .models.user import Subs
    from .models.user import UserSubs
    from .models.user import Transaction
    from .models.user import Role
    from .models.user import UserRoles
    from .models.user import UserInvitation
    from .models.version import Version
    from .models.job import Job
    from .models.setting import Setting
    from .models.apikey import ApiKey
    from .models.access import Access
    from .models.status import Status
    from .models.stats import Stats
    from .models.db_stats import DBStats

    func_db.drop_all()
    func_db.session.commit()


# noinspection PyUnresolvedReferences
def db_create():
    current_app.logger.info("db create {}".format(current_app.config["DB_HOST"]))

    from .models.audit import Audit
    from .models.user import User
    from .models.user import Role
    from .models.user import UserRoles
    from .models.user import Subs
    from .models.user import UserSubs
    from .models.user import Transaction
    from .models.user import UserInvitation
    from .models.version import Version
    from .models.job import Job
    from .models.setting import Setting
    from .models.apikey import ApiKey
    from .models.access import Access
    from .models.status import Status
    from .models.stats import Stats
    from .models.db_stats import DBStats

    func_db.create_all()
    func_db.session.commit()


def db_init():
    from .models.version import Version
    from .models.user import User
    from .models.user import Role
    from .models.apikey import ApiKey

    user_manager = current_app.user_manager

    my_db_model_ver = 0
    my_ssk_model_ver = 0
    my_version = Version()
    my_version.db_version = my_db_model_ver
    my_version.ssk_version = my_ssk_model_ver

    current_app.logger.info("db init {} db ver {} ssk db v {}".format(current_app.config["DB_HOST"],
                                                                      my_db_model_ver,
                                                                      my_ssk_model_ver))

    my_admin_api = ApiKey()
    my_admin_api.key = str(uuid.uuid4())

    from .models.setting import Setting
    my_collector_setting = Setting()
    my_collector_setting.system = True
    my_collector_setting.key = "MAX_COLLECTORS"
    my_collector_setting.type = SettingParser.INT_TYPE
    my_collector_setting.value = current_app.config["MAX_COLLECTORS"]

    my_max_active_keys_setting = Setting()
    my_max_active_keys_setting.system = True
    my_max_active_keys_setting.key = "MAX_ACTIVE_KEYS"
    my_max_active_keys_setting.type = SettingParser.INT_TYPE
    my_max_active_keys_setting.value = current_app.config["MAX_ACTIVE_KEYS"]

    my_active_now_setting = Setting()
    my_active_now_setting.system = True
    my_active_now_setting.key = "API_ACTIVE_NOW"
    my_active_now_setting.type = SettingParser.INT_TYPE
    my_active_now_setting.value = current_app.config["API_ACTIVE_NOW"]

    my_website_open_setting = Setting()
    my_website_open_setting.system = True
    my_website_open_setting.key = "WEBSITE_OPEN"
    my_website_open_setting.type = SettingParser.BOOL_TYPE
    my_website_open_setting.value = current_app.config["WEBSITE_OPEN"]

    my_sched_on_setting = Setting()
    my_sched_on_setting.system = True
    my_sched_on_setting.key = "SCHED_ON"
    my_sched_on_setting.type = SettingParser.BOOL_TYPE
    my_sched_on_setting.value = current_app.config["SCHED_ON"]

    my_admin_user = User()
    my_admin_user.username = current_app.config['ADMIN_NAME']
    my_admin_user.email = current_app.config['ADMIN_EMAIL']
    my_admin_user.first_name = "Indiana"
    my_admin_user.last_name = "Jones"
    my_admin_user.email_confirmed_at = datetime.now()
    my_admin_user.password = user_manager.hash_password(truncate_password(current_app.config['ADMIN_PASS']))
    my_admin_user.api_keys.append(my_admin_api)
    my_admin_user.user_settings.append(my_collector_setting)
    my_admin_user.user_settings.append(my_max_active_keys_setting)
    my_admin_user.user_settings.append(my_active_now_setting)
    my_admin_user.user_settings.append(my_website_open_setting)
    my_admin_user.user_settings.append(my_sched_on_setting)

    my_admin_role = Role()
    my_admin_role.name = current_app.config['ADMIN_GROUP_NAME']
    my_admin_role.users.append(my_admin_user)

    my_free_user = User()
    my_free_user.username = current_app.config['USER_FREE_NAME']
    my_free_user.email = current_app.config['USER_FREE_EMAIL']
    my_free_user.first_name = "John"
    my_free_user.last_name = "Free"
    my_free_user.email_confirmed_at = datetime.now()
    my_free_user.password = user_manager.hash_password(truncate_password(current_app.config['USER_FREE_PASS']))

    my_pro_user = User()
    my_pro_user.username = current_app.config['USER_PRO_NAME']
    my_pro_user.email = current_app.config['USER_PRO_EMAIL']
    my_pro_user.first_name = "John"
    my_pro_user.last_name = "Pro"
    my_pro_user.email_confirmed_at = datetime.now()
    my_pro_user.password = user_manager.hash_password(truncate_password(current_app.config['USER_PRO_PASS']))

    my_user_role = Role()
    my_user_role.name = current_app.config['USER_GROUP_NAME']
    my_user_role.users.append(my_free_user)
    my_user_role.users.append(my_pro_user)

    # ver 8
    from .models.user import Subs
    my_free_subs = Subs()
    my_free_subs.name = current_app.config['FREE_SUB']
    my_free_subs.users.append(my_free_user)

    my_pro_subs = Subs()
    my_pro_subs.name = current_app.config['PRO_SUB']
    my_pro_subs.users.append(my_pro_user)
    my_pro_subs.users.append(my_admin_user)

    func_db.session.add(my_version)
    func_db.session.add(my_admin_user)
    func_db.session.add(my_free_user)
    func_db.session.add(my_pro_user)
    func_db.session.commit()
