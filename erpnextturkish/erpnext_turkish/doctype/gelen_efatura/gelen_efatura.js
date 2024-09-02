// Copyright (c) 2024, Logedosoft Business Solutions and contributors
// For license information, please see license.txt

function get_incoming_invoices(frm) {
	frappe.call({
		method: "erpnextturkish.td_utils.get_incoming_invoices",
		freeze: true,
		freeze_message: __("Logedo is running..."),
		args: {
			doc: frm.doc
		},
		callback: function (r) {
			console.log(r);
			frappe.msgprint(objResponse.message.result);
			if (r.message.op_result == false) {
				frappe.show_alert({
					message: r.message.op_message,
					indicator: 'red'
				}, 5);
				//frappe.throw(r.message.op_message);
			} else {
				frappe.model.sync(r.message.doc);
				frm.dirty();
				frm.refresh();
				frappe.show_alert({
					message: r.message.op_message,
					indicator: r.message.op_indicator || 'green'
				}, 5);
			}			
		},
	});
}

frappe.ui.form.on("Gelen EFatura", {
	refresh(frm) {
		frm.add_custom_button(__("Faturayı İncele"), function () {
			frappe.msgprint("ALERT");
		});

		frm.add_custom_button(__("Yenile"), function () {
			frappe.msgprint("ALERT");
		});

		get_incoming_invoices(frm);
	},
});
