// Copyright (c) 2024, Logedosoft Business Solutions and contributors
// For license information, please see license.txt

frappe.ui.form.on('TD Utils', {
	execute_item_reorder_check: function(frm) {
		frappe.call({
			method: 'erpnextturkish.erpnext_turkish.doctype.td_utils.td_utils.trigger_auto_reorder',
			callback: function(r) {
				console.log(r);
			}
		});
	}
});
