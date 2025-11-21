#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


from flask import current_app
from sqlalchemy import desc
from ..utils import get_safe_string

from ..models.contact import Contact
import uuid


class ContactMgr:
    _db_session = None

    def __init__(self, a_db_session):
        self._db_session = a_db_session

    def commit(self):
        self._db_session.commit()

    def get_all_keys(self):
        my_db_list = list(self._db_session.query(Contact).order_by(desc(Contact.created)))

        my_ret_val = [my_tmp.req_id for my_tmp in my_db_list]

        return my_ret_val

    def add_post(self, a_name, an_email, a_message, a_source):
        my_ret_val = False
        my_ret_mesg = "Error: cannot add contact {}".format(a_name)

        my_req = self._db_session.query(Contact).filter(Contact.email == an_email).first()
        if my_req is None:
            try:
                my_request = Contact()
                my_request.req_id = str(uuid.uuid4())
                my_request.name = a_name
                my_request.email = an_email
                my_request.details = a_message
                my_request.source = a_source
                my_request.sent = False

                self._db_session.add(my_request)

                my_ret_val = True
                my_ret_mesg = '[[ print "OK: contact {} added" ]]'.format(my_request.req_id)
            except Exception:
                current_app.logger.error("Cannot add contact %s", get_safe_string(a_name))
        else:
            my_ret_mesg = '{} please be patient. We have your request already.'.format(my_req.email)

        return my_ret_val, my_ret_mesg
