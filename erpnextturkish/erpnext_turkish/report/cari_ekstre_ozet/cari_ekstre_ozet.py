# Copyright (c) 2013, Logedosoft Business Solutions and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, erpnext
from erpnext import get_company_currency, get_default_company
from erpnext.accounts.report.utils import get_currency, convert_to_presentation_currency
from frappe.utils import getdate, cstr, flt, fmt_money
from frappe import _, _dict

def execute(filters=None):
	if not filters:
		return [], []

	columns, data = [], []

	if validate_filters(filters):

		columns = get_columns(filters)

		frappe.db.sql("""SET group_concat_max_len=2048;""")

		data = frappe.db.sql(
			"""
			SELECT 
				BELGE_TARIHI, BELGE_SAATI, TIP, ACIKLAMA, BORC, ALACAK
			FROM 
				LD_CARI_EKSTRE_OZET
			WHERE 
				SIRKET = %(company)s
				AND CARI_KODU = %(party)s

			UNION ALL

			SELECT
				'' AS BELGE_TARIHI,
				'' AS BELGE_SAATI,
				'' AS TIP,
				'' AS ACIKLAMA,
				SUM(BORC) AS BORC, SUM(ALACAK) AS ALACAK
			FROM 
				LD_CARI_EKSTRE_OZET
			WHERE 
				SIRKET = %(company)s
				AND CARI_KODU = %(party)s
			"""
			, filters, as_dict=1)

	return columns, data

def validate_filters(filters):
	blnResult = True

	if not filters.get('company'):
		frappe.throw(_('{0} is mandatory').format(_('Company')))

	if not filters.get('party'):
		blnResult = False

	return blnResult
		
def get_columns(filters):
	if filters.get("company"):
		currency = get_company_currency(filters["company"])
	else:
		company = get_default_company()
		currency = get_company_currency(company)

	columns = [
		{
			"label": _("Posting Date"),
			"fieldname": "BELGE_TARIHI",
			"fieldtype": "date",
			"width": 90
		},
		{
			"label": _("Posting Time"),
			"fieldname": "BELGE_SAATI",
			"fieldtype": "Time",
			"width": 90
		},
		{
			"label": _("Voucher Type"),
			"fieldname": "TIP",
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Remark"),
			"fieldname": "ACIKLAMA",
			"fieldtype": "Data",
			"width": 400
		},
		{
			"label": _("Debit"),
			"fieldname": "BORC",
			"fieldtype": "Float",
			"width": 100
		},
		{
			"label": _("Credit"),
			"fieldname": "ALACAK",
			"fieldtype": "Float",
			"width": 100
		}
	]

	return columns