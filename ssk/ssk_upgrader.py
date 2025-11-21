#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#

from datetime import datetime

from flask import current_app
from flask_user import user_manager
from sqlalchemy import create_engine

from ssk.db import get_db, get_version, set_ssk_version, func_db
from ssk.globals.setting_parser import SettingParser
from ssk.models.setting import Setting
from ssk.models.user import User


class SSKUpgrader:
    _to_skip = []
    UPGRADING_MESG = "upgrading to {}"

    @staticmethod
    def ver1():
        my_version = 1
        current_app.logger.info(SSKUpgrader.UPGRADING_MESG.format(my_version))

        SSKUpgrader._to_skip.append(2)
        SSKUpgrader._to_skip.append(3)
        SSKUpgrader._to_skip.append(4)
        SSKUpgrader._to_skip.append(5)
        SSKUpgrader._to_skip.append(6)
        SSKUpgrader._to_skip.append(8)

        set_ssk_version(my_version)

    @staticmethod
    def ver2():
        my_version = 2
        current_app.logger.info(SSKUpgrader.UPGRADING_MESG.format(my_version))

        my_db_version = get_version()

        if my_db_version.ssk_version < my_version and my_version not in SSKUpgrader._to_skip:
            my_engine = create_engine(current_app.config['SQLALCHEMY_BINDS']['logdb'])
            my_engine.execute('alter table access add column response_time INTEGER')

        set_ssk_version(my_version)

    @staticmethod
    def ver3():
        my_version = 3
        current_app.logger.info(SSKUpgrader.UPGRADING_MESG.format(my_version))

        my_db_version = get_version()

        if my_db_version.ssk_version < my_version and my_version not in SSKUpgrader._to_skip:
            get_db().engine.execute('alter table notes add column summary VARCHAR(100)')
            get_db().engine.execute('alter table notes add column category VARCHAR(100)')

        set_ssk_version(my_version)

    @staticmethod
    def ver4():
        my_version = 4
        current_app.logger.info(SSKUpgrader.UPGRADING_MESG.format(my_version))

        my_db_version = get_version()

        if my_db_version.ssk_version < my_version and my_version not in SSKUpgrader._to_skip:
            get_db().engine.execute('alter table notes add column meta VARCHAR(100)')

        set_ssk_version(my_version)

    @staticmethod
    def ver5():
        my_version = 5
        current_app.logger.info(SSKUpgrader.UPGRADING_MESG.format(my_version))

        my_db_version = get_version()

        if my_db_version.ssk_version < my_version and my_version not in SSKUpgrader._to_skip:
            # noinspection PyUnresolvedReferences
            from .models.stats import Stats
            get_db().create_all()

        set_ssk_version(my_version)

    @staticmethod
    def ver6():
        my_version = 6
        current_app.logger.info(SSKUpgrader.UPGRADING_MESG.format(my_version))

        my_db_version = get_version()

        if my_db_version.ssk_version < my_version and my_version not in SSKUpgrader._to_skip:
            # noinspection PyUnresolvedReferences
            from .models.db_stats import DBStats
            get_db().create_all()

        set_ssk_version(my_version)

    @staticmethod
    def ver7():
        my_version = 7
        current_app.logger.info(SSKUpgrader.UPGRADING_MESG.format(my_version))

        my_db_version = get_version()

        if my_db_version.ssk_version < my_version and my_version not in SSKUpgrader._to_skip:
            my_sched_on_setting = Setting()
            my_sched_on_setting.system = True
            my_sched_on_setting.key = "SCHED_ON"
            my_sched_on_setting.type = SettingParser.BOOL_TYPE
            my_sched_on_setting.value = current_app.config["SCHED_ON"]

            my_admin_email = current_app.config["ADMIN_EMAIL"]
            from ssk.models.user import User
            my_admin_user = User.get_by_email(my_admin_email)
            my_admin_user.user_settings.append(my_sched_on_setting)
            get_db().session.commit()

        set_ssk_version(my_version)

    @staticmethod
    def ver8():
        my_version = 8
        current_app.logger.info(SSKUpgrader.UPGRADING_MESG.format(my_version))

        my_db_version = get_version()

        if my_db_version.ssk_version < my_version and my_version not in SSKUpgrader._to_skip:
            # noinspection PyUnresolvedReferences
            from .models.user import Subs, UserSubs, Transaction
            get_db().create_all()

            my_pro_user = User()
            my_pro_user.username = current_app.config['USER_PRO_NAME']
            my_pro_user.email = current_app.config['USER_PRO_EMAIL']
            my_pro_user.first_name = "John"
            my_pro_user.last_name = "Pro"
            my_pro_user.email_confirmed_at = datetime.now()
            from ssk.db import truncate_password
            my_pro_user.password = user_manager.hash_password(truncate_password(current_app.config['USER_PRO_PASS']))

            my_admin_user = User.get_by_email(current_app.config["ADMIN_EMAIL"])
            my_free_user = User.get_by_email(current_app.config["USER_PRO_EMAIL"])

            my_free_subs = Subs()
            my_free_subs.name = current_app.config['FREE_SUB']
            my_free_subs.users.append(my_free_user)

            my_pro_subs = Subs()
            my_pro_subs.name = current_app.config['PRO_SUB']
            my_pro_subs.users.append(my_pro_user)
            my_pro_subs.users.append(my_admin_user)

            func_db.session.add(my_admin_user)
            func_db.session.add(my_free_user)
            func_db.session.add(my_pro_user)
            func_db.session.commit()

        set_ssk_version(my_version)

    @staticmethod
    def get_upgrade_functions():
        my_retval = [SSKUpgrader.ver1, SSKUpgrader.ver2, SSKUpgrader.ver3, SSKUpgrader.ver4, SSKUpgrader.ver5,
                     SSKUpgrader.ver6, SSKUpgrader.ver7, SSKUpgrader.ver8]

        return my_retval
