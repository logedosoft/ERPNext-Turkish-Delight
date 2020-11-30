frappe.ui.form.on('Delivery Note', {
    setup: function (frm) {

    },
    onload: function (frm) {
        add_irsaliye_btns(frm)
    },
    refresh: function (frm) {
        add_irsaliye_btns(frm)
    },
})

var add_irsaliye_btns = function(frm) {
    if (frm.doc.docstatus != 1 || frm.doc.is_return) {
        return
    }
    frm.add_custom_button(__('Gönder E Irsaliye'), function () {
        frappe.call({
            method: 'erpnextturkish.eirsaliye.api.eirsaliye.send_eirsaliye',
            args: {
                'delivery_note_name': frm.doc.name
            },
            callback: function (data) {
                if (data.message) {
                    frm.reload_doc()
                    console.log(data.message)
                }
            }
        });
    });
    frm.add_custom_button(__('Vaildate E Irsaliye'), function () {
        frappe.call({
            method: 'erpnextturkish.eirsaliye.api.eirsaliye.validate_eirsaliye',
            args: {
                'delivery_note_name': frm.doc.name
            },
            callback: function (data) {
                if (data.message) {
                    frm.reload_doc()
                    console.log(data.message)
                }
            }
        });
    });
}