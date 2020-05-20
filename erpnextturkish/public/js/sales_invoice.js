//strOperation = Send (EFatura Gonderimi), Refresh (E-Faturanin son durumunu alir)
function EInvoiceProcess(frm, strOperation) {
    let strMethod = "";
    let objArgs = {}
    
    if (strOperation == "Send") {
        strMethod = "erpnextturkish.td_utils.send_einvoice";
        objArgs = { strSalesInvoiceName: frm.docname }
    } else if (strOperation == "Refresh") {
        strMethod = "erpnextturkish.td_utils.get_invoice_status";
        objArgs = { strSaleInvoiceName: frm.docname }
    }

    frappe.call({
        method: strMethod,
        async: true,
        args: objArgs
    })
    .then((objResponse) => {
        console.log(objResponse);
        frm.reload_doc();
        if (strOperation == "Send") {
            frappe.msgprint(objResponse.message.result);
        } else if (strOperation == "Refresh") {
            frm.scroll_to_field("td_efatura_durumu");
        }
    });
}

frappe.ui.form.on("Sales Invoice", {
	refresh: (frm) => {

        if (frm.doc.docstatus == 1 && !(cint(frm.doc.is_return) && frm.doc.return_against)) {
			frm.add_custom_button(__('Gönder'),
				function() {
                    EInvoiceProcess(frm, "Send");
                }, __('E-Fatura'));
            frm.add_custom_button(__('Durum Güncelle'),
				function() {
                    EInvoiceProcess(frm, "Refresh");
                }, __('E-Fatura'));
			frm.page.set_inner_btn_group_as_primary(__('E-Fatura'));
		}
    }
});