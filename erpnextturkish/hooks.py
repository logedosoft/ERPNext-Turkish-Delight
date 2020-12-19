# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "erpnextturkish"
app_title = "ERPNext Turkish"
app_publisher = "Logedosoft Business Solutions"
app_description = "E-Fatura ve diger ozel cozumler"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "info@logedosoft.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/erpnextturkish/css/erpnextturkish.css"
app_include_js = "/assets/js/to_console.min.js"

# include js, css files in header of web template
# web_include_css = "/assets/erpnextturkish/css/erpnextturkish.css"
# web_include_js = "/assets/erpnextturkish/js/erpnextturkish.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}
doctype_js = {
    "Purchase Order": "public/js/purchase_order.js",
    "Sales Invoice": "public/js/sales_invoice.js",
	"Customer": "public/js/customer.js",
	"Delivery Note": "eirsaliye/api/delivery_note.js"
}
# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "erpnextturkish.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "erpnextturkish.install.before_install"
# after_install = "erpnextturkish.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "erpnextturkish.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
 	"Delivery Note": {
 		"on_submit": "erpnextturkish.eirsaliye.api.eirsaliye.on_submit_validate",
	}
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"erpnextturkish.tasks.all"
# 	],
# 	"daily": [
# 		"erpnextturkish.tasks.daily"
# 	],
# 	"hourly": [
# 		"erpnextturkish.tasks.hourly"
# 	],
# 	"weekly": [
# 		"erpnextturkish.tasks.weekly"
# 	]
# 	"monthly": [
# 		"erpnextturkish.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "erpnextturkish.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "erpnextturkish.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "erpnextturkish.task.get_dashboard_data"
# }

fixtures = [
	{"doctype":"Custom Field", "filters": [["name", "in", (
		"Delivery Note-e_irsaliye_section",
		"Delivery Note-eirsaliye_uuid",
		"Delivery Note-belgeno",
		"Customer-ld_tax_office",
		"Delivery Note-yenidengonderilebilirmi",
		"Delivery Note-gonderimcevabidetayi",
		"Delivery Note-gonderimcevabikodu",
		"Delivery Note-gonderimdurumu",
		"Delivery Note-yerelbelgeoid",
		"Delivery Note-durum",
		"Delivery Note-column_break_20",
		"Delivery Note-ld_note"
	)]]},
	{"doctype":"Property Setter", "filters": [["name", "in", (
	
	)]]},
]