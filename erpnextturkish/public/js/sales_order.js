//Sales Order Customizations
frappe.ui.form.on("Sales Order", {
    onload_post_render: (frm) => {
        if(frm.doc.status !== 'Closed' && frm.doc.status !== 'On Hold' && frm.doc.docstatus == 1) {
            frm.add_custom_button(__("Manufacture"), () => {
                frappe.call({
                    method: 'erpnextturkish.selling.api.selling_utils.get_work_order_items',
                    args: {
                        strSalesOrder: frm.docname
                    },
                    callback: (r) => {
                        if(!r.message) {
                            frappe.msgprint({
                                title: __('Item Fetch Failed'),
                                message: __(r.message),
                                indicator: 'orange'
                            });
                            return;
                        } else {
                            const fields = [
                            {
                                fieldtype: 'Link',
                                fieldname: 's_warehouse',
                                options: 'Warehouse',
                                reqd: 1,
                                label: __('Select Source Warehouse'),
                                in_list_view: 1,
                            },
                            {
                                fieldtype: 'Link',
                                fieldname: 't_warehouse',
                                options: 'Warehouse',
                                reqd: 1,
                                label: __('Select Target Warehouse'),
                                in_list_view: 1,
                            },
                            {
                                label: 'Items',
                                fieldtype: 'Table',
                                fieldname: 'items',
                                description: __('Select BOM and Qty for Production'),
                                fields: [
                                {
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
                                    frm.call({
                                        method: 'erpnextturkish.selling.api.selling_utils.create_manufacture_se_for_so',
                                        args: {
                                            items: data,
                                            company: frm.doc.company,
                                            sales_order: frm.docname,
                                            s_warehouse: data.s_warehouse,
                                            t_warehouse: data.t_warehouse
                                        },
                                        freeze: true,
                                        callback: function(r) {
                                            if(r.message) {
                                                frappe.msgprint({
                                                    message: __('Stock Entries Created: {0}',
                                                        [r.message.map(function(d) {
                                                            return repl('<a href="#Form/Stock Entry/%(name)s">%(name)s</a>', {name:d})
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
                        frappe.msgprint({
                            title: __('Getting BOM info failed'),
                            message: __('Details: {0}', [r]), 
                            indicator: 'red'
                        });
                    }
                })
            });
        }
    }
});