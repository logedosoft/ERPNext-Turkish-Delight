# -*- coding: utf-8 -*-
# LOGEDOSOFT

from __future__ import unicode_literals
import frappe, json
from frappe import msgprint, _

from frappe.model.document import Document
from frappe.utils import cstr, flt, cint, nowdate, add_days, comma_and, now_datetime, ceil, today, formatdate, format_time, encode, get_time

from erpnextturkish import console

@frappe.whitelist()
def get_work_order_items(strSalesOrder):
    docSO = frappe.get_doc("Sales Order", strSalesOrder)

    return docSO.get_work_order_items()