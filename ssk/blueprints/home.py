#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#

import csv
import os

from flask import (Blueprint, request, Response, send_file, current_app)
from flask import render_template

from ssk.forms.contact_form import ContactForm
from ssk.ssk_consts import SSK_ADMIN_GROUP
from ssk.globals.web_gate import WebGate

from ssk.lg import get_logic

from ssk.blueprints.home_handler import HomeHandler


bp = Blueprint('home', __name__, url_prefix='/ssk')


@bp.route('/closed', methods=['GET'])
def closed():
    return WebGate.render_closed()


@bp.route('/', methods=['GET'])
def index():
    if WebGate.is_closed():
        return WebGate.render_closed()

    return render_template("local/start.html", admin_group_name=SSK_ADMIN_GROUP)


@bp.route('/tasks', methods=['GET'])
def tasks():
    if WebGate.is_closed():
        return WebGate.render_closed()

    my_file, my_tasks = HomeHandler.tasks()

    return render_template(my_file, tasks=my_tasks, admin_group_name=SSK_ADMIN_GROUP)


@bp.route('/blog/<string:note>', methods=['GET'])
def blog(note):
    if WebGate.is_closed():
        return WebGate.render_closed()

    my_note_path = "local/notes/{}.html".format(note)
    try:
        my_form = ContactForm()
        my_form.source = "note {}".format(note)

        return render_template("local/notebook.html",
                           toshow=my_note_path,
                           form=my_form,
                           message=None,
                           admin_group_name=SSK_ADMIN_GROUP)
    except Exception as err:
        current_app.logger.error(f"ERROR: note not found {my_note_path} {err}")

        return WebGate.render_notfound()


@bp.route('/blog_posts', methods=['GET'])
def blog_posts():
    if WebGate.is_closed():
        return WebGate.render_closed()

    my_template_path = current_app.jinja_loader.searchpath[0]
    my_meta_path = "{}/local/notes/meta.csv".format(my_template_path)

    my_posts = []
    with open(my_meta_path) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count > 0:
                my_posts.append({"note": row[1], "title": row[2], "subtitle": row[3], "created": row[4], "labels": row[5]})
            line_count += 1

    return render_template("ssk/posts.html",
                           posts=my_posts,
                           admin_group_name=SSK_ADMIN_GROUP)


@bp.route('/tasks_action', methods=['POST'])
def tasks_action():
    _, my_tasks = HomeHandler.tasks_action(request)

    return render_template("ssk/tasks.html", tasks=my_tasks, admin_group_name=SSK_ADMIN_GROUP)


@bp.route('/task_log_download/<string:a_tid>')
def task_log_download(a_tid):
    my_logfile = get_logic().get_job_mgr().get_logfile(a_tid)

    if my_logfile is not None and os.path.exists(my_logfile):
        return send_file(my_logfile, as_attachment=True)


@bp.route('/progress/<string:a_thread_id>')
def progress(a_thread_id):
    def generate(a_job_tracker, a_tid):
        my_progress = a_job_tracker.get_progress(a_tid)
        yield "data:" + str(my_progress) + "\n\n"

    return Response(generate(get_logic().get_job_mgr(), a_thread_id), mimetype='text/event-stream')


@bp.route('/about', methods=['GET'])
def about():
    if WebGate.is_closed():
        return WebGate.render_closed()

    my_form = ContactForm()
    my_form.source = "about"

    return render_template("ssk/about.html", form=my_form, message=None, admin_group_name=SSK_ADMIN_GROUP)


@bp.route('/post_contact', methods=['POST'])
def post_contact():
    if WebGate.is_closed():
        return WebGate.render_closed()

    my_page, my_form, my_message = HomeHandler.post_contact(request)

    return render_template(my_page, form=my_form, message=my_message, admin_group_name=SSK_ADMIN_GROUP)
