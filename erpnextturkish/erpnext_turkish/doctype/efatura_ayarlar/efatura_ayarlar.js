// Copyright (c) 2019, Logedosoft Business Solutions and contributors
// For license information, please see license.txt

frappe.ui.form.on('EFatura Ayarlar', {
	btn_login_test: function(frm) {
		frappe.call({
			method:"erpnextturkish.td_utils.login_test"
			})
		.then((objResponse) => {
			console.log(objResponse);
			frappe.msgprint(objResponse.message.result);
		});	
	}
});
