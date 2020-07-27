// Copyright (c) 2016, Logedosoft Business Solutions and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Cari Ekstre Ozet"] = {
	"filters": [
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company"),
			"reqd": 1
		},
		{
			"fieldname":"party_type",
			"label": __("Party Type"),
			"fieldtype": "Link",
			"options": "Party Type",
			"default": "Customer",
			on_change: function() {
				frappe.query_report.set_filter_value('party', "");
			}
		},
		{
			"fieldname":"party",
			"label": __("Party"),
			"fieldtype": "MultiSelectList",
			"reqd": 1,
			get_data: function(txt) {
				if (!frappe.query_report.filters) return;

				let party_type = frappe.query_report.get_filter_value('party_type');
				if (!party_type) return;

				return frappe.db.get_link_options(party_type, txt);
			},
			on_change: function() {
				var party_type = frappe.query_report.get_filter_value('party_type');
				var parties = frappe.query_report.get_filter_value('party');

				if(!party_type || parties.length === 0 || parties.length > 1) {
					frappe.query_report.set_filter_value('party_name', "");
					frappe.query_report.set_filter_value('tax_id', "");
					return;
				} else {
					var party = parties[0];
					/*var fieldname = erpnext.utils.get_party_name(party_type) || "name";
					frappe.db.get_value(party_type, party, fieldname, function(value) {
						frappe.query_report.set_filter_value('party_name', value[fieldname]);
					});*/

					if (party_type === "Customer" || party_type === "Supplier") {
						frappe.db.get_value(party_type, party, "tax_id", function(value) {
							frappe.query_report.set_filter_value('tax_id', value["tax_id"]);
						});
					}
				}
			}
		},
		{
			"fieldname":"tax_id",
			"label": __("Tax Id"),
			"fieldtype": "Data",
			"hidden": 0
		},
		{
			"fieldname": "presentation_currency",
			"label": __("Currency"),
			"fieldtype": "Select",
			"default": "TRY",
			"options": erpnext.get_presentation_currency_list()
		}
	]
};
