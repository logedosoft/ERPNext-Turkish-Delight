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

frappe.ui.form.on('Sales Invoice', {
    refresh(frm) {
        if (frm.doc.docstatus === 1) {
            frappe.db.get_list('TD EInvoice Settings', {
                filters: { company: frm.doc.company },
                fields: ['name', 'integrator']
            }).then(settings_list => {
                if (settings_list && settings_list.length > 0) {
                    const settings = settings_list[0];

                    frappe.db.get_value('TD EInvoice Integrator', settings.integrator, 'td_enable')
                        .then(result => {
                            if (result?.message?.td_enable) {
                                // ❌ Bu satırı kaldırdık:
                                // frm.add_custom_button(__('E-Invoice'), null, __('Actions'));

                                // ✅ Sadece işlevsel butonları ekle:
                                frm.add_custom_button(__('Send'), () => {
                                    frappe.call({
                                        method: 'erpnextturkish.td_utils.send_invoice_to_finalizer',
                                        args: { invoice_name: frm.doc.name },
                                        callback(r) {
                                            if (!r.exc) {
                                                const result = r.message;
                                                frappe.msgprint({
                                                    title: result.status === 'success' ? __('Success') : __('Send Error'),
                                                    indicator: result.status === 'success' ? 'green' : 'red',
                                                    message: result.status === 'success'
                                                        ? '✅' + __('Invoice sent successfully')
                                                        : `❌ ${result.error || __('Send failed')}`
                                                });
                                                frm.reload_doc();
                                            }
                                        }
                                    });
                                }, __('E-Invoice'));

                                frm.add_custom_button(__('Update Status'), () => {
                                    frappe.call({
                                        method: 'erpnextturkish.td_utils.update_invoice_status',
                                        args: { invoice_name: frm.doc.name },
                                        callback(r) {
                                            if (!r.exc) {
                                                if (r.message.op_result == false) {
                                                    frappe.msgprint({
                                                        title: __("Durum Güncelleme Hatası"),
                                                        indicator: "red",
                                                        message: r.message.op_message
                                                    });
                                                } else {
                                                    frm.set_value('gib_status', r.message.op_message);
                                                    frappe.show_alert({
                                                        message: __("Fatura Durumu:") + "<br>" + r.message.op_message,
                                                        indicator: "green"
                                                    });
                                                }
                                            }
                                        }
                                    });
                                }, __('E-Invoice'));
                            }
                        });
                }
            });
        }
    }
});
