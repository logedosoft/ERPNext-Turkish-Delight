# Copyright (c) 2024, Logedosoft Business Solutions and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class TDUtils(Document):
	pass

@frappe.whitelist()
def trigger_auto_reorder():
	from erpnext.stock.reorder_item import reorder_item
	
	reorder_item()
	frappe.msgprint("Auto Re-Order is triggered!")
