#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


from flask import current_app
from sqlalchemy import and_
from ..db import get_db
from ssk.globals.setting_parser import SettingParser


class AppSettings:
    ERROR_KEY_EMPTY = "Key cannot be empty"

    _globals = {}

    def get_setting(self, a_key, an_owners_email=None):
        from ssk.models.all_ssk_db import User
        from ssk.models.all_ssk_db import Setting
        my_ret_val = None

        if an_owners_email is not None:
            my_user = User.get_by_email(an_owners_email)
            if my_user is not None:
                my_setting = Setting.get_by_owner_key(my_user.id, a_key)

                if my_setting is not None:
                    my_ret_val = SettingParser.parse(my_setting.type, my_setting.value)
        else:
            if a_key not in self._globals.keys():
                my_setting = Setting.get_by_key(a_key)

                if my_setting is not None:
                    my_ret_val = SettingParser.parse(my_setting.type, my_setting.value)
                    self._globals[a_key] = my_ret_val
            else:
                my_ret_val = self._globals[a_key]

        return my_ret_val

    def del_setting(self, an_owners_email, a_key):
        from ssk.models.all_ssk_db import User
        from ssk.models.all_ssk_db import Setting

        my_ret_val = False

        my_user = User.get_by_email(an_owners_email)
        if my_user is None:
            return False, "Error: User {} not found".format(an_owners_email)

        if a_key == "":
            return False, AppSettings.ERROR_KEY_EMPTY

        from ..db import get_db
        my_setting = get_db().session.query(Setting).filter(and_(Setting.key == a_key,
                                                                 Setting.user_id == my_user.id)).first()

        if my_setting is not None:
            if not my_setting.system:
                get_db().session.delete(my_setting)
                get_db().session.commit()
                my_ret_val = True
                my_ret_mesg = "OK: {} removed".format(a_key)
            else:
                my_ret_mesg = "Error: Cannot remove system settings"
        else:
            my_ret_mesg = "Error: {} not found".format(a_key)

        return my_ret_val, my_ret_mesg

    def set_global(self, a_key, a_value):
        from ssk.models.all_ssk_db import User
        from ssk.models.all_ssk_db import Setting

        my_ret_val = False

        if a_key == "":
            return False, AppSettings.ERROR_KEY_EMPTY

        my_admin_user = get_db().session.query(User).filter(User.username == current_app.config["ADMIN_NAME"]).first()
        if my_admin_user is not None:
            my_setting = get_db().session.query(Setting).filter(and_(Setting.key == a_key,
                                                                     Setting.user_id == my_admin_user.id)).first()

            if my_setting is not None:
                my_setting.system = a_value
                get_db().session.add(my_setting)
                get_db().session.commit()

                if my_setting.system and a_key not in self._globals.keys():
                    self._globals[a_key] = my_setting.value

                my_ret_val = True
                my_ret_mesg = "OK: {} system changed to {}".format(a_key, a_value)
            else:
                my_ret_mesg = "Error: {} not found".format(a_key)
        else:
            my_ret_mesg = "Error: {} admin user not found".format(a_key)

        return my_ret_val, my_ret_mesg

    def is_global(self, a_key):
        from ssk.models.all_ssk_db import User
        from ssk.models.all_ssk_db import Setting

        my_ret_val = False
        my_ret_mesg = "OK: {} is NOT a system conf".format(a_key)

        if a_key == "":
            return False, AppSettings.ERROR_KEY_EMPTY

        my_admin_user = get_db().session.query(User).filter(User.username == current_app.config["ADMIN_NAME"]).first()
        if my_admin_user is not None:
            my_setting = get_db().session.query(Setting).filter(and_(Setting.key == a_key,
                                                                     Setting.user_id == my_admin_user.id)).first()

            if my_setting:
                if my_setting.system:
                    my_ret_val = True
                    my_ret_mesg = "OK: {} is a system conf".format(a_key)
            else:
                my_ret_mesg = "Error: setting {} not found".format(a_key)
        else:
            my_ret_mesg = "Error: {} admin user not found".format(a_key)

        return my_ret_val, my_ret_mesg

    def set_setting(self, an_owners_email, a_key, a_type, a_value):
        from ssk.models.all_ssk_db import User
        from ssk.models.all_ssk_db import Setting

        my_user = User.get_by_email(an_owners_email)
        if my_user is None:
            return False, "Error: User {} not found".format(an_owners_email)

        if a_key == "":
            return False, AppSettings.ERROR_KEY_EMPTY

        if not SettingParser.is_valid(a_type):
            return False, "Error: Invalid Type {}".format(a_type)

        if a_value == "":
            return False, "Error: Value cannot be empty"

        my_value = SettingParser.parse(a_type, a_value)
        if my_value is None:
            return False, "Error: Value {} cannot be parsed".format(a_value)

        my_setting = get_db().session.query(Setting).filter(and_(Setting.key == a_key,
                                                                 Setting.user_id == my_user.id)).first()

        if my_setting is not None:
            my_old_value = my_setting.value
            my_setting.value = my_value
            my_setting.type = a_type

            get_db().session.add(my_setting)
            get_db().session.commit()

            if my_setting.system:
                self._globals[a_key] = my_value

            my_ret_val = True
            my_ret_mesg = "OK: {} changed from {} to {}".format(a_key, my_old_value, my_value)
        else:
            my_setting = Setting()
            my_setting.key = a_key
            my_setting.type = a_type
            my_setting.value = a_value

            my_user.user_settings.append(my_setting)
            get_db().session.commit()

            my_ret_val = True
            my_ret_mesg = "OK: {} added. Value set to {}".format(a_key, my_value)

        return my_ret_val, my_ret_mesg
