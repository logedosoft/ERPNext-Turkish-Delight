//Sales Order Customizations
frappe.ui.form.on("Sales Order", {
    onload_post_render: (frm) => {
        if(frm.doc.status !== 'Closed') {
            if(frm.doc.status !== 'On Hold') {
                frm.add_custom_button(__("Manufacture23"), () => {
                    frappe.call({
                        method: 'erpnextturkish.selling.api.selling_utils.get_work_order_items',
                        args: {
                            strSalesOrder: frm.docname
                        },
                        callback: (r) => {
                            console.log(r);
                            if(!r.message) {
                                frappe.msgprint({
                                    title: __('Work Order not created'),
                                    message: __('No Items with Bill of Materials to Manufacture'),
                                    indicator: 'orange'
                                });
                                return;
                            }
                            else if(!r.message) {
                                frappe.msgprint({
                                    title: __('Work Order not created'),
                                    message: __('Work Order already created for all items with BOM'),
                                    indicator: 'orange'
                                });
                                return;
                            } else {
                                const fields = [{
                                    label: 'Items',
                                    fieldtype: 'Table',
                                    fieldname: 'items',
                                    description: __('Select BOM and Qty for Production'),
                                    fields: [{
                                        fieldtype: 'Read Only',
                                        fieldname: 'item_code',
                                        label: __('Item Code'),
                                        in_list_view: 1
                                    }, {
                                        fieldtype: 'Link',
                                        fieldname: 'bom',
                                        options: 'BOM',
                                        reqd: 1,
                                        label: __('Select BOM'),
                                        in_list_view: 1,
                                        get_query: function (doc) {
                                            return { filters: { item: doc.item_code } };
                                        }
                                    }, {
                                        fieldtype: 'Float',
                                        fieldname: 'pending_qty',
                                        reqd: 1,
                                        label: __('Qty'),
                                        in_list_view: 1
                                    }, {
                                        fieldtype: 'Data',
                                        fieldname: 'sales_order_item',
                                        reqd: 1,
                                        label: __('Sales Order Item'),
                                        hidden: 1
                                    }],
                                    data: r.message,
                                    get_data: () => {
                                        return r.message
                                    }
                                }]
                                var d = new frappe.ui.Dialog({
                                    title: __('Select Items to Manufacture'),
                                    fields: fields,
                                    primary_action: function() {
                                        var data = d.get_values();
                                        me.frm.call({
                                            method: 'make_work_orders',
                                            args: {
                                                items: data,
                                                company: me.frm.doc.company,
                                                sales_order: me.frm.docname,
                                                project: me.frm.project
                                            },
                                            freeze: true,
                                            callback: function(r) {
                                                if(r.message) {
                                                    frappe.msgprint({
                                                        message: __('Work Orders Created: {0}',
                                                            [r.message.map(function(d) {
                                                                return repl('<a href="#Form/Work Order/%(name)s">%(name)s</a>', {name:d})
                                                            }).join(', ')]),
                                                        indicator: 'green'
                                                    })
                                                }
                                                d.hide();
                                            }
                                        });
                                    },
                                    primary_action_label: __('Create')
                                });
                                d.show();
                            }
                        },
                        error: (r) => {
                            alert("Hata oluştu." + r)
                        }
                    })
                });
            }
        }
    }
});