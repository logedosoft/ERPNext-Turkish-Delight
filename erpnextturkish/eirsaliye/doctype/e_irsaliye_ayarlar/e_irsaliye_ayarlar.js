// Copyright (c) 2020, Logedosoft Business Solutions and contributors
// For license information, please see license.txt

frappe.ui.form.on('E Irsaliye Ayarlar', {
	btn_login_test: function(frm){
        if (frm.is_dirty()) {
            frm.save()
        }
		frappe.call({
            method: 'erpnextturkish.eirsaliye.api.eirsaliye.login_test',
            args: {
                'eirsaliye_settings': frm.doc.name,
            },
            callback: function (data) {
                if (data.message) {
                    // frm.reload_doc()
                    console.table(data.message)
                    // show_msg(data)
                }
            }
        });
	}
});
