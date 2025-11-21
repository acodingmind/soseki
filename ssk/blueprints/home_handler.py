#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


from flask_login import current_user
from ssk import AppSettings, get_logic, get_db
from ssk.globals.contacts_mgr import ContactMgr
from ssk.forms.contact_form import ContactForm


class HomeHandler(object):
    PAGE_CLOSED = "ssk/closed.html"
    PAGE_TASKS = "ssk/tasks.html"
    PAGE_NOTES = "ssk/notes.html"
    PAGE_ABOUT = "ssk/about.html"

    @staticmethod
    def tasks():
        my_tasks = []

        if AppSettings().get_setting("LOGIN_OFF"):
            return HomeHandler.PAGE_CLOSED, my_tasks

        if not current_user.is_anonymous:
            my_jobs = get_logic().get_job_mgr().get_all_jobs_by_user(current_user.id)

            for my_temp_task in my_jobs:
                my_tasks.append({"tid": my_temp_task.task_id,
                                 "name": my_temp_task.name,
                                 "details": my_temp_task.started.strftime("%d-%b-%Y %H:%M:%S"),
                                 "status": my_temp_task.status,
                                 "prog": my_temp_task.progress})

        return HomeHandler.PAGE_TASKS, my_tasks

    @staticmethod
    def tasks_action(a_request):
        my_tasks = []

        if AppSettings().get_setting("LOGIN_OFF"):
            return HomeHandler.PAGE_CLOSED, my_tasks

        if a_request.method == 'POST':
            my_job_mgr = get_logic().get_job_mgr()

            my_job_to_stop = a_request.form.get('stop')
            if my_job_to_stop is not None:
                my_job_mgr.stop_job(my_job_to_stop)

            my_job_to_delete = a_request.form.get('delete')
            if my_job_to_delete is not None:
                my_job_mgr.delete_job(my_job_to_delete)

        if not current_user.is_anonymous:
            my_jobs = get_logic().get_job_mgr().get_all_jobs_by_user(current_user.id)

            for my_temp_task in my_jobs:
                my_tasks.append({"tid": my_temp_task.task_id,
                                 "name": my_temp_task.name,
                                 "details": my_temp_task.started.strftime("%d-%b-%Y %H:%M:%S"),
                                 "status": my_temp_task.status,
                                 "prog": my_temp_task.progress})

        return HomeHandler.PAGE_TASKS, my_tasks

    @staticmethod
    def post_contact(a_request):
        my_thank_you = None
        if a_request.method == 'POST':
            my_thank_you = "Thank You. We will contact you shortly"

            my_source = a_request.form.get("source")
            my_name = a_request.form.get("name")
            my_email = a_request.form.get("email")
            my_details = a_request.form.get("message")

            my_db_session = get_db().session
            my_contact_mgr = ContactMgr(my_db_session)
            my_ret_val, my_message = my_contact_mgr.add_post(my_name, my_email, my_details, my_source)
            if my_ret_val:
                my_contact_mgr.commit()
            else:
                my_thank_you = my_message

        return HomeHandler.PAGE_ABOUT, ContactForm(), my_thank_you
