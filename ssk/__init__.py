#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#

import time
from logging.handlers import RotatingFileHandler

import yaml
from blinker import ANY
from flask.cli import with_appcontext
from flask import render_template, flash, request
from flask_login import current_user
from apscheduler.schedulers.background import BackgroundScheduler
from ssk.utils import set_const

import os
import click
from flask import current_app
import uuid

from .config import Config, get_log_level
from .globals.cmd_processor import CmdProcessor
from .globals.app_settings import AppSettings
from flask_login import logout_user
from flask_login.signals import user_logged_in, user_logged_out

from .lg import get_logic

from .db import get_db, truncate_password
from datetime import datetime

# Monkey-patch bcrypt.hashpw at the lowest level to handle 72-byte limit
# This must happen BEFORE passlib tries to use bcrypt
import bcrypt as _bcrypt_module
_original_bcrypt_hashpw = _bcrypt_module.hashpw
def _patched_bcrypt_hashpw(password, salt):
    """Patched bcrypt.hashpw that truncates passwords to 72 bytes."""
    if isinstance(password, str):
        password = password.encode('utf-8')
    if len(password) > 72:
        password = password[:72]
    return _original_bcrypt_hashpw(password, salt)
_bcrypt_module.hashpw = _patched_bcrypt_hashpw

# Also monkey-patch Flask-User's UserManager.hash_password
from flask_user import UserManager
_original_usermanager_hash_password = UserManager.hash_password
def _patched_hash_password(self, password):
    """Patched hash_password that truncates passwords to 72 bytes for bcrypt."""
    return _original_usermanager_hash_password(self, truncate_password(password))
UserManager.hash_password = _patched_hash_password

from .logic.jobs.db_cleanup_job import DbCleanupJob
from .logic.jobs.db_stat_job import DbStatJob
from .logic.jobs.health_check_job import HealthCheckJob
from .logic.jobs.page_stat_job import PageStatJob
from .models.audit import Audit
from .ssk_consts import SSK_ADMIN_GROUP

import logging
from flask import g


@user_logged_in.connect_via(ANY)
def user_logged_in(sender, user, **extra):
    if user.username != current_app.config["ADMIN_NAME"]:
        my_login_off = AppSettings().get_setting("LOGIN_OFF")
        if my_login_off is not None and my_login_off is True:
            logout_user()
            flash('Sorry, we are currently closed for the maintenance', 'error')
    else:
        user.last_login = datetime.now()

        if user.num_of_logins is not None:
            user.num_of_logins = user.num_of_logins + 1
        else:
            user.num_of_logins = 1

        user.loggedin = 1

        get_db().session.add(user)
        get_db().session.commit()


@user_logged_out.connect_via(ANY)
def user_logged_out(sender, user, **extra):
    user.loggedin = 0
    get_db().session.add(user)
    get_db().session.commit()


def request_error(e):
    my_error_id = str(uuid.uuid4())
    current_app.logger.error("{} {} {} {}".format(my_error_id, request.full_path, e.code, e.name, ))

    return render_template('error.html', error_id=my_error_id), 400


def internal_server_error(e):
    my_error_id = str(uuid.uuid4())
    current_app.logger.fatal("{} {}".format(my_error_id, e))

    return render_template('500.html', error_id=my_error_id), 500


def set_meta():
    from ssk.models.version import Version

    if "DB_CURR" not in current_app.config.keys() or "SSK_DB_CURR" not in current_app.config.keys():
        my_version_record = get_db().session.query(Version).order_by(Version.id.desc()).first()
        current_app.config["SSK_DB_CURR"] = my_version_record.ssk_version
        current_app.config["DB_CURR"] = my_version_record.db_version

    return {"meta": {"APP_NAME": current_app.config["USER_APP_NAME"],
                     "APP_PROFILE": current_app.config["PROFILE"],
                     "LG_VERSION": get_logic().get_id(),
                     "APP_VERSION": current_app.config["USER_APP_VERSION"],
                     "SSK_VERSION": current_app.config["SSK_VER"],
                     "DB_VERSION": current_app.config["DB_CURR"],
                     "SSK_DB_VERSION": current_app.config["SSK_DB_CURR"],
                     "LATEST_DB_VERSION": current_app.config["DB_MODEL_VERSION"],
                     "LATEST_SSK_DB_VERSION": current_app.config["SSK_DB_MODEL_VERSION"],
                     }}


def start_apigate():
    from .globals.api_gate import ApiGate
    ApiGate.init()
    ApiGate.load()


def start_settings():
    from .globals.app_settings import AppSettings
    from .globals.setting_parser import SettingParser

    my_admin_email = current_app.config["ADMIN_EMAIL"]
    my_value = current_app.config["WEBSITE_OPEN"]

    AppSettings().set_setting(my_admin_email, "WEBSITE_OPEN", SettingParser.BOOL_TYPE, my_value)


def after_request(response):
    if current_app.config["LOG_ALL_REQUESTS"]:
        my_response = int((time.time() - g.start) * 1000)
        if my_response > current_app.config["LOG_SLOWER_THAN"] or response.status_code >= 400:
            from ssk.models.access import Access
            my_access = Access()
            my_access.remote_addr = request.remote_addr
            my_access.method = request.method
            my_access.protocol = request.scheme
            my_access.path = request.full_path[:250]
            my_access.response = response.status

            my_access.response_time = my_response
            my_access.user = ""

            if not current_user.is_anonymous:
                my_access.user = current_user.username

            get_db().session.add(my_access)
            get_db().session.commit()

    return response


def every_request():
    if current_app.config["LOG_ALL_REQUESTS"]:
        g.start = time.time()

    my_user = current_user

    if not my_user.is_anonymous:
        if my_user.username != current_app.config["ADMIN_NAME"]:
            my_login_off = AppSettings().get_setting("WEBSITE_OPEN")
            if my_login_off is not None and my_login_off is False:
                logout_user()
                flash('Sorry, we are currently closed for the maintenance', 'error')
        else:
            from ssk.models.all_ssk_db import User
            my_user.last_access = datetime.now()

            get_db().session.add(my_user)
            get_db().session.commit()


def start_cmd_processor():
    my_max_collectors = current_app.config["MAX_COLLECTORS"]

    if my_max_collectors > 0:
        CmdProcessor.start(a_job_mgr=get_logic().get_job_mgr(),
                           a_logger=current_app.logger,
                           a_max_collectors=my_max_collectors)


def exec_cmd(a_cmd):
    with a_cmd.get_current_app().app_context():
        if AppSettings().get_setting("SCHED_ON"):
            a_cmd.write_to_audit("OK", "scheduler triggers")
            a_cmd.work()
        else:
            a_cmd.write_to_audit("NOK", "scheduler paused")


def start_scheduler():
    my_scheduler = BackgroundScheduler(daemon=True)
    my_minutes = 60
    current_app.logger.info("scheduling HealthCheckJob every {} minutes".format(my_minutes))
    my_health = HealthCheckJob(current_app, a_args=["health"])
    my_scheduler.add_job(exec_cmd, 'interval', minutes=my_minutes, args=[my_health])

    current_app.logger.info("scheduling PageStatJob every {} minutes".format(my_minutes))
    my_page_stat = PageStatJob(current_app, a_args=["stats"])
    my_scheduler.add_job(exec_cmd, 'interval', minutes=my_minutes, args=[my_page_stat])

    current_app.logger.info("scheduling DbStatJob every {} minutes".format(my_minutes))
    my_db_stat = DbStatJob(current_app, a_args=["dbstats"])
    my_scheduler.add_job(exec_cmd, 'interval', minutes=my_minutes, args=[my_db_stat])

    if "DB_CLEANUP" in current_app.config.keys():
        my_to_clean = current_app.config["DB_CLEANUP"]

        for my_tmp_table in my_to_clean.keys():
            current_app.logger.info("scheduling cleanup of {}".format(my_tmp_table))
            my_task = DbCleanupJob(current_app, a_args=["dbcleanup {}".format(my_tmp_table),
                                                        my_tmp_table,
                                                        my_to_clean[my_tmp_table]])

            my_scheduler.add_job(exec_cmd, 'interval', minutes=360, args=[my_task])

    my_scheduler.start()


def init_ssk(an_app, a_bus_logic, a_db_upgrader, a_testing):
    my_app = an_app
    my_app.db_upgrader = a_db_upgrader
    my_app.bus_logic = a_bus_logic

    flask_env = os.getenv("FLASK_ENV", None)
    my_profile = flask_env
    if a_testing:
        my_profile = "tst"

    my_app_config = os.getenv("SSK_CONFIG", None)
    if my_app_config is None:
        # Try multiple possible config locations
        possible_paths = [
            'app/cfg/{}.yaml'.format(my_profile),
            'cfg/{}.yaml'.format(my_profile),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                my_app_config = path
                break
        
        if my_app_config is None:
            raise FileNotFoundError(
                f"Configuration file not found. Tried: {possible_paths}. "
                "Please set SSK_CONFIG environment variable to your config file path."
            )

    my_config_obj = Config()
    with open(my_app_config, 'r') as my_config:
        my_app_config = yaml.safe_load(stream=my_config)

        for my_tmp_key in my_app_config['ssk'].keys():
            my_type = list(my_app_config['ssk'][my_tmp_key].keys())[0]
            my_yaml_value = my_app_config['ssk'][my_tmp_key][my_type]
            my_value = set_const(my_tmp_key, my_yaml_value, my_type)
            my_config_obj.__setattr__(my_tmp_key, my_value)

    my_log_dir = my_config_obj.__getattribute__("LOG_DIR")
    if not os.path.exists(my_log_dir):
        os.mkdir(my_log_dir)

    my_config_obj.__setattr__("LOG_FILE", os.path.join(my_log_dir, my_config_obj.__getattribute__("LOG_FILE_NAME")))
    my_config_obj.__setattr__("SQLALCHEMY_BINDS", {'logdb': my_config_obj.__getattribute__("LOG_DB_CONNSTR")})

    my_app.config.from_object(my_config_obj)

    my_log_level = get_log_level(my_app)
    logging.basicConfig(handlers=[RotatingFileHandler(my_app.config["LOG_FILE"], maxBytes=5000000, backupCount=10)],
                        level=my_log_level,
                        format="[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
    logging.getLogger('werkzeug').setLevel(my_log_level)

    my_app.logger.info("init_ssk {} start".format(ssk_consts.SSK_VER))

    if not os.path.exists(my_app.config["DATA_FOLDER"]):
        os.mkdir(my_app.config["DATA_FOLDER"])

    my_app.cli.add_command(clean_db_command)
    my_app.cli.add_command(create_db_command)
    my_app.cli.add_command(setup_db_command)
    my_app.cli.add_command(init_command)

    my_app.register_error_handler(500, internal_server_error)
    my_app.register_error_handler(400, request_error)
    my_app.register_error_handler(403, request_error)
    my_app.register_error_handler(404, request_error)
    my_app.register_error_handler(405, request_error)
    my_app.register_error_handler(410, request_error)

    from .db import close_db, close_logdb
    my_app.teardown_appcontext(close_db)
    my_app.teardown_appcontext(close_logdb)

    from .db import func_db
    func_db.init_app(my_app)

    my_app.before_request(every_request)
    my_app.after_request(after_request)

    my_app.context_processor(set_meta)

    from .models.user import User
    from .models.user import UserInvitation
    from flask_user import UserManager, EmailManager
    my_app.user_manager = UserManager(my_app, func_db, User, UserInvitationClass=UserInvitation)
    my_app.user_manager.email_manager = EmailManager(my_app)
    my_app.meta = {"PROFILE": os.getenv("FLASK_ENV", None)}

    from .blueprints import home
    my_app.register_blueprint(home.bp)

    from .blueprints import api
    my_app.register_blueprint(api.bp)

    from .blueprints import cmd
    my_app.register_blueprint(cmd.bp)

    from .blueprints import admin
    my_app.register_blueprint(admin.bp)

    my_app.logger.info("init_ssk end")

    return my_app


def start_ssk(an_app, a_testing):
    with an_app.app_context():
        an_app.logger.info("start_ssk start")

        with an_app.app_context():
            from .db import db_version_check
            db_version_check()

        if not a_testing:
            start_cmd_processor()
        start_apigate()
        # it has to be after db init
        start_scheduler()
        start_settings()

        an_app.logger.info("start_ssk end")


@click.command('clean-db')
@with_appcontext
def clean_db_command():
    """Clear the existing data and tables."""
    from . import db
    db.db_clean()
    click.echo('Database {} Removed'.format(current_app.config["DB_HOST"]))


@click.command('create-db')
@with_appcontext
def create_db_command():
    """Clear the existing data and create new tables."""
    from . import db
    db.db_create()
    click.echo('Database {} Created'.format(current_app.config["DB_HOST"]))


@click.command('setup-db')
@with_appcontext
def setup_db_command():
    """Setup initial config."""
    from . import db
    db.db_init()
    click.echo('Database {} Initialized'.format(current_app.config["DB_HOST"]))


@click.command('init')
@click.argument('app_name', required=False, default='app')
def init_command(app_name):
    """Initialize a new Soseki application with standard folder structure."""
    import os
    import shutil
    
    if os.path.exists(app_name):
        click.echo(f'Error: Directory "{app_name}" already exists')
        return
    
    # Get the path to the blanco_app template
    blanco_app_path = os.path.join(os.path.dirname(__file__), 'blanco_app')
    
    if not os.path.exists(blanco_app_path):
        click.echo(f'Error: Template directory not found at {blanco_app_path}')
        return
    
    # Copy the entire blanco_app directory
    try:
        shutil.copytree(blanco_app_path, app_name)
        click.echo(f'Created: {app_name}/ (from template)')
        
        # Get the parent directory where app_name is being created
        parent_dir = os.path.dirname(os.path.abspath(app_name))
        
        # Copy bin directory next to app folder
        blanco_bin_path = os.path.join(os.path.dirname(__file__), 'blanco_bin')
        bin_dest = os.path.join(parent_dir, 'bin')
        
        if os.path.exists(blanco_bin_path):
            if os.path.exists(bin_dest):
                shutil.rmtree(bin_dest)
            shutil.copytree(blanco_bin_path, bin_dest)
            click.echo(f'Created: bin/ (from template)')
        
        # Copy jup directory next to app folder
        blanco_jup_path = os.path.join(os.path.dirname(__file__), 'blanco_jup')
        jup_dest = os.path.join(parent_dir, 'jup')
        
        if os.path.exists(blanco_jup_path):
            if os.path.exists(jup_dest):
                shutil.rmtree(jup_dest)
            shutil.copytree(blanco_jup_path, jup_dest)
            click.echo(f'Created: jup/ (from template)')
        
        # List created structure
        for root, dirs, files in os.walk(app_name):
            level = root.replace(app_name, '').count(os.sep)
            indent = ' ' * 2 * level
            click.echo(f'{indent}{os.path.basename(root)}/')
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                click.echo(f'{subindent}{file}')
        
        click.echo(f'\nSuccessfully initialized Soseki blanco application in "{app_name}/"')
        click.echo(f'\nNext steps:')
        click.echo(f'  # Edit cfg/lite.yaml with your settings')
        click.echo(f'  ./bin/run_app.sh')
        
    except Exception as e:
        click.echo(f'Error: Failed to create application: {e}')
