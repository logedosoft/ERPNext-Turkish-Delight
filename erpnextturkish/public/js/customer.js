//strOperation = Send (EFatura Gonderimi), Refresh (E-Faturanin son durumunu alir)
function EInvoiceProcess(frm, strOperation) {
    let strMethod = "";
    let objArgs = {}
    
    if (strOperation == "GetUserAliasses") {
        strMethod = "erpnextturkish.td_utils.get_user_aliasses";
        objArgs = { strCustomerName: frm.docname }
    }

    frappe.call({
        method: strMethod,
        async: true,
        args: objArgs
    })
    .then((objResponse) => {
        console.log(objResponse);
        if (strOperation == "GetUserAliasses") {
            frappe.msgprint(objResponse.message.result);
            frm.reload_doc();
        }
    });
}

frappe.ui.form.on("Customer", {
    td_btn_alias_guncelle: (frm) => {
        EInvoiceProcess(frm, "GetUserAliasses")
    }
});