function SendEInvoice(frm) {
    console.log(frm.doc.docname);
    frappe.call({
        method:"erpnextturkish.td_utils.send_einvoice",
        async: true,
        args: { strSalesInvoiceName: frm.docname }
    })
    .then((objResponse) => {
        console.log(objResponse);
        frm.reload_doc();
        frappe.msgprint(objResponse.message.result);
    });
}

frappe.ui.form.on("Sales Invoice", {
	refresh: (frm) => {

        if (frm.doc.docstatus == 1 && !(cint(frm.doc.is_return) && frm.doc.return_against)) {
			frm.add_custom_button(__('Gönder'),
				function() {
                    SendEInvoice(frm);
                }, __('E-Fatura'));
			frm.page.set_inner_btn_group_as_primary(__('E-Fatura'));
		}
    }
});