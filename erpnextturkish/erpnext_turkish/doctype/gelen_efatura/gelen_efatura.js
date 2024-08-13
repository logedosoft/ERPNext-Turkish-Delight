// Copyright (c) 2024, Logedosoft Business Solutions and contributors
// For license information, please see license.txt

frappe.ui.form.on("Gelen EFatura", {
	refresh(frm) {
		frm.add_custom_button(__("Faturayı İncele"), function () {
			frappe.msgprint("ALERT");
		});
	},
});
