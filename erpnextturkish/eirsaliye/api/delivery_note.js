frappe.ui.form.on('Delivery Note', {
    setup: function (frm) {

    },
    onload: function (frm) {
        add_irsaliye_btn(frm)
    },
    refresh: function (frm) {
        
    },
})

var add_irsaliye_btn = function(frm) {
    if (frm.doc.docstatus != 1) {
        return
    }
    frm.add_custom_button(__('Gönder E Irsaliye'), function () {
        // if (frm.is_dirty()) {
        //     frm.save();
        // }
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
}