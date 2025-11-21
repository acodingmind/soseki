#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField, StringField, HiddenField
from wtforms.validators import DataRequired, Email


class ContactForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    message = TextAreaField("Additional Information")
    submit = SubmitField("Please contact me")
    source = HiddenField("source")
