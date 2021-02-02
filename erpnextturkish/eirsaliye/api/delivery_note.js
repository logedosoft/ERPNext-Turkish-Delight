frappe.ui.form.on('Delivery Note', {
    setup: function (frm) {

    },
    onload: function (frm) {
        //add_irsaliye_btns(frm)
    },
    refresh: function (frm) {
        add_irsaliye_btns(frm);
    },
})

var add_irsaliye_btns = function(frm) {
    if (frm.doc.docstatus != 1 || frm.doc.is_return) {
        return
    }
    frm.add_custom_button(__('Gönder'), function () {
        frappe.call({
            method: 'erpnextturkish.eirsaliye.api.eirsaliye.send_eirsaliye',
            args: {
                'delivery_note_name': frm.doc.name
            },
            callback: function (data) {
                console.log(data);
                if (data.message) {
                    frm.reload_doc()
                    console.table(data.message)
                    show_msg(data)
                }
            }
        });
    }, __("E-İrsaliye"));
    frm.add_custom_button(__('Durum Güncelle'), function () {
        frappe.call({
            method: 'erpnextturkish.eirsaliye.api.eirsaliye.validate_eirsaliye',
            args: {
                'delivery_note_name': frm.doc.name
            },
            callback: function (data) {
                if (data.message) {
                    frm.reload_doc()
                    console.table(data.message)
                    show_msg(data)
                }
            }
        });
    }, __("E-İrsaliye"));

    frm.page.set_inner_btn_group_as_primary(__('E-İrsaliye'));
}

var show_msg = function(data) {
    if (data.message.belgeNo) {
        frappe.msgprint({
            title: __('Success'),
            indicator: 'green',
            message: __('Delivery Note Registered Successfully with number {0}.', [data.message.belgeNo])
        });
    }
    else if (data.message.durum == 1){
        frappe.msgprint({
            title: __('Wating'),
            indicator: 'blue',
            message: __(`Processing has not finished, please try again later!`)
        });
    }
    else if (data.message.durum || data.message.aciklama){
        frappe.msgprint({
            title: __('Error'),
            indicator: 'red',
            message: data.message.aciklama || data.message.durum 
        });
    }
    else if (data.message.faultcode || data.message.faultstring) {
        frappe.msgprint({
            title: __('Error'),
            indicator: 'red',
            message: __('Server returned: {0}.{1}', [data.message.faultcode, data.message.faultstring])
        });
    }
    else {
        frappe.msgprint({
            title: __('Error'),
            indicator: 'red',
            message: __('Server returned: {0}', [data.message])
        });
    }
}