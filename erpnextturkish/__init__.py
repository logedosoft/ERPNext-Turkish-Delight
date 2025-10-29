# -*- coding: utf-8 -*-
from __future__ import unicode_literals

__version__ = '1.250711.7'

def console(*data):
	import frappe
	frappe.publish_realtime('out_to_console', data, user=frappe.session.user)
