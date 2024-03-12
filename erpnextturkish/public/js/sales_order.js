/*LOGEDOSOFT-2024*/
//Sales Order Customizations

function show_production_plan(frm) {
    frappe.call({
        method: "erpnext.selling.doctype.sales_order.sales_order.get_work_order_items",
        args: {
            sales_order: frm.docname
        },
        freeze: true,
        callback: function (r) {
            if (!r.message) {
                frappe.msgprint({
                    title: __('Work Order not created'),
                    message: __('No Items with Bill of Materials to Manufacture'),
                    indicator: 'orange'
                });
                return;
            }
            else {
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
                    title: __('Select Items for Production Plan'),
                    fields: fields,
                    primary_action: function () {
                        //Get selected items
                        let arrSelectectedItems = { items: d.fields_dict.items.grid.get_selected_children() };
                        frappe.new_doc("Production Plan", { "get_items_from": "Sales Order" }, docPP => {
                            docPP.posting_date = frappe.datetime.get_today();
                            docPP.customer = frm.doc.customer;
                            //Create Sales Order row in PP
                            let rowSO = frappe.model.add_child(docPP, "sales_orders");
                            rowSO.customer = frm.doc.customer;
                            rowSO.grand_total = frm.doc.base_grand_total;
                            rowSO.sales_order = frm.docname;
                            rowSO.sales_order_date = frm.doc.delivery_date;

                            //Create Production Plan Items from selected items in dialog
                            arrSelectectedItems.items.forEach(selected_item => {
                                console.log(doc.po_items);
                                console.log(doc.po_items[0].item_code);
                                if (!docPP.po_items[0].item_code) {
                                    let rowItem = docPP.items[0];
                                } else {
                                    let rowItem = frappe.model.add_child(docPP, "po_items");
                                }
                                rowItem.item_code = selected_item.item_code;
                                rowItem.bom_no = selected_item.bom;
                                rowItem.planned_qty = selected_item.pending_qty;
                                rowItem.pending_qty = selected_item.pending_qty;
                                rowItem.warehouse = selected_item.warehouse;
                                //rowItem.stock_uom = "";
                                //rowItem.planned_start_date = "";
                                rowItem.sales_order_item = selected_item.sales_order_item;
                                rowItem.sales_order = frm.docname;
                            });
                        });
                        d.hide();
                    },
                    primary_action_label: __('Create')
                });
                d.show();
            }
        }
    });
}

frappe.ui.form.on("Sales Order", {
    refresh: (frm) => {
        if(frm.doc.status !== 'Closed' && frm.doc.status !== 'On Hold' && frm.doc.docstatus == 1) {
            //Add production plan if enabled
            frappe.db.get_single_value("TD Utils", "create_pp_from_so").then((blnPPEnabled) => {
                if (blnPPEnabled) {
                    frm.add_custom_button(__("Production Plan"), () => {
                        show_production_plan(frm);
                    }, __('Create'));
                }
            });

            //Create Stock Entry from Sales Order
            frappe.db.get_single_value("TD Utils", "create_manufacture_str_from_so").then((blnManufactureSTEEnabled) => {
                if (blnManufactureSTEEnabled) {
                    frm.add_custom_button(__("Manufacture"), () => {

                        let promSourceWH = frappe.db.get_single_value('ERPNext Turkish Settings', 'def_source_w_settings');
                        let promTargetWH = frappe.db.get_single_value('ERPNext Turkish Settings', 'def_target_w_settings');

                        Promise.all([promSourceWH, promTargetWH]).then((values) => {
                            let strSourceWH = values[0];
                            let strTargetWH = values[1];

                            frappe.call({
                                method: 'erpnextturkish.selling.api.selling_utils.get_work_order_items',
                                args: {
                                    strSalesOrder: frm.docname
                                },
                                callback: (r) => {
                                    console.log(r);
                                    if (!r.message) {
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
                                                default: strSourceWH
                                            },
                                            {
                                                fieldtype: 'Link',
                                                fieldname: 't_warehouse',
                                                options: 'Warehouse',
                                                reqd: 1,
                                                label: __('Select Target Warehouse'),
                                                in_list_view: 1,
                                                default: strTargetWH
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
                                            primary_action: function () {
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
                                                    btn: $('.primary-action'),
                                                    freeze: true,
                                                    callback: function (r) {
                                                        console.log(r);
                                                        if (r.message) {
                                                            console.log(r.message);
                                                            frappe.msgprint({
                                                                message: __('Stock Entries Created: Click {0} to list them.<br>Created Stock Entries:{1}',
                                                                    [
                                                                        repl('<a href="#List/Stock Entry/List?ld_sales_order=%(name)s">here</a>', { name: frm.docname }),
                                                                        r.message.map(function (key) {
                                                                            console.log(key);
                                                                            return repl('<a href="#Form/Stock Entry/%(name)s">%(name)s</a>', { name: key })
                                                                        }).join(', ')
                                                                    ]),
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

                    }, __('Create'));
                }
            });
        }
    }
});