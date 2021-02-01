# Copyright (c) 2020, Logedosoft Business Solutions and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from jinja2 import Environment, FileSystemLoader, BaseLoader
import os
import requests
import hashlib
import base64



def to_base64(value):
    data_bytes = value.encode('utf-8')
    data = base64.b64encode(data_bytes)
    return str(data)[2:-1]


def get_hash_md5(value):
    return hashlib.md5(value.encode()).hexdigest()


def render_template(context, file_name=None, file=None):
    if file_name:
        path=os.path.join(os.path.dirname(__file__),'./')
        templateLoader = FileSystemLoader(searchpath=path)
        templateEnv = Environment(loader=templateLoader)
        template = templateEnv.get_template(file_name)
    elif file:
        template = Environment(loader=BaseLoader).from_string(file)
    else:
        frappe.throw(_("Missing file name or file to render with Jinja Temlate"))
    
    outputText = template.render(context=context)
    return outputText