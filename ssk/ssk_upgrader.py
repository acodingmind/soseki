#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#

from datetime import datetime

from flask import current_app
from sqlalchemy import inspect, text

from ssk.db import get_db, get_version, set_ssk_version, func_db
from ssk.globals.setting_parser import SettingParser
from ssk.models.setting import Setting
from ssk.models.user import User


class SSKUpgrader:
    _to_skip = []
    UPGRADING_MESG = "upgrading to {}"

    @staticmethod
    def _add_column(an_engine, a_table, a_column, a_type):
        """ALTER TABLE ... ADD COLUMN, skipped when the table is missing or already has the column."""
        my_inspector = inspect(an_engine)
        if a_table not in my_inspector.get_table_names():
            current_app.logger.info("table {} not found, {} not added".format(a_table, a_column))
            return

        if a_column in [my_col["name"] for my_col in my_inspector.get_columns(a_table)]:
            return

        with an_engine.begin() as my_conn:
            my_conn.execute(text("ALTER TABLE {} ADD COLUMN {} {}".format(a_table, a_column, a_type)))

    @staticmethod
    def ver1():
        my_version = 1
        current_app.logger.info(SSKUpgrader.UPGRADING_MESG.format(my_version))

        SSKUpgrader._to_skip.append(2)
        SSKUpgrader._to_skip.append(3)
        SSKUpgrader._to_skip.append(4)
        SSKUpgrader._to_skip.append(5)
        SSKUpgrader._to_skip.append(6)
        SSKUpgrader._to_skip.append(7)
        SSKUpgrader._to_skip.append(8)

        set_ssk_version(my_version)

    @staticmethod
    def ver2():
        my_version = 2
        current_app.logger.info(SSKUpgrader.UPGRADING_MESG.format(my_version))

        my_db_version = get_version()

        if my_db_version.ssk_version < my_version and my_version not in SSKUpgrader._to_skip:
            SSKUpgrader._add_column(get_db().engines['logdb'], 'access', 'response_time', 'INTEGER')

        set_ssk_version(my_version)

    @staticmethod
    def ver3():
        my_version = 3
        current_app.logger.info(SSKUpgrader.UPGRADING_MESG.format(my_version))

        my_db_version = get_version()

        if my_db_version.ssk_version < my_version and my_version not in SSKUpgrader._to_skip:
            SSKUpgrader._add_column(get_db().engine, 'notes', 'summary', 'VARCHAR(100)')
            SSKUpgrader._add_column(get_db().engine, 'notes', 'category', 'VARCHAR(100)')

        set_ssk_version(my_version)

    @staticmethod
    def ver4():
        my_version = 4
        current_app.logger.info(SSKUpgrader.UPGRADING_MESG.format(my_version))

        my_db_version = get_version()

        if my_db_version.ssk_version < my_version and my_version not in SSKUpgrader._to_skip:
            SSKUpgrader._add_column(get_db().engine, 'notes', 'meta', 'VARCHAR(100)')

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

        my_has_sched_on = Setting.query.filter_by(key="SCHED_ON").first() is not None
        if my_db_version.ssk_version < my_version and my_version not in SSKUpgrader._to_skip \
                and not my_has_sched_on:
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
            from .models.user import Role, Subs, UserSubs, Transaction
            from ssk.db import truncate_password
            get_db().create_all()

            # same users and subscriptions a new database gets in db_init(); safe to run more than once
            my_pro_user = User.get_by_email(current_app.config['USER_PRO_EMAIL'])
            if my_pro_user is None:
                my_pro_user = User()
                my_pro_user.username = current_app.config['USER_PRO_NAME']
                my_pro_user.email = current_app.config['USER_PRO_EMAIL']
                my_pro_user.first_name = "John"
                my_pro_user.last_name = "Pro"
                my_pro_user.email_confirmed_at = datetime.now()
                my_pro_user.password = current_app.user_manager.hash_password(
                    truncate_password(current_app.config['USER_PRO_PASS']))

                my_user_role = Role.query.filter_by(name=current_app.config['USER_GROUP_NAME']).first()
                if my_user_role is not None:
                    my_user_role.users.append(my_pro_user)

                func_db.session.add(my_pro_user)

            my_admin_user = User.get_by_email(current_app.config["ADMIN_EMAIL"])
            my_free_user = User.get_by_email(current_app.config["USER_FREE_EMAIL"])

            for my_sub_name, my_members in ((current_app.config['FREE_SUB'], [my_free_user]),
                                            (current_app.config['PRO_SUB'], [my_pro_user, my_admin_user])):
                my_subs = Subs.query.filter_by(name=my_sub_name).first()
                if my_subs is None:
                    my_subs = Subs()
                    my_subs.name = my_sub_name
                    func_db.session.add(my_subs)

                for my_member in my_members:
                    if my_member is not None and my_member not in my_subs.users:
                        my_subs.users.append(my_member)

            func_db.session.commit()

        set_ssk_version(my_version)

    @staticmethod
    def get_upgrade_functions():
        my_retval = [SSKUpgrader.ver1, SSKUpgrader.ver2, SSKUpgrader.ver3, SSKUpgrader.ver4, SSKUpgrader.ver5,
                     SSKUpgrader.ver6, SSKUpgrader.ver7, SSKUpgrader.ver8]

        return my_retval
