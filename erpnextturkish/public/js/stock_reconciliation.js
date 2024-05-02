/* LOGEDOSOFT 2024*/
//Stock Reconciliation customizations
function save_template_data(frm, template_data, row) {
	//#ROW ILE DEVAM ET
	//Will save template data to the current Stock Reconciliation items table
	//Remove the lines if custom_ld_variant_selector_name is not empty
	//Then find proper item codes and create new lines based on the selected data
	frappe.call({
		method: "erpnextturkish.td_utils.get_template_item_info",
		args: {
			doc: frm.doc,
			template_data: template_data
		},
		callback: (r) => {
			console.log(r);
			//frappe.model.sync(r.message);
			//frm.dirty();
			frm.refresh_field("items");
		}
	});
}

async function get_template_data(template_item_code) {
	//Will return attributes of the selected item template. (IE possible values)
	return await frappe.call({
		method: "erpnextturkish.td_utils.get_item_template_attributes",
		args: {
			strTemplateItemCode: template_item_code
		},
		callback: (r) => {
			if (r.message.op_result === false) {
				frappe.throw(r.message.op_message);
			} else {
				return r;
			}
		}
	})
}

function ShowVariantSelectorDialog(frm, cdt, cdn, row) {
	//Shows a dialog about possible values of the selected item template
	get_template_data(row.item_template).then((template_data) => {
		template_data = template_data.message;
		console.log(template_data);
		let variant_fields = [];
		variant_fields.push({
			fieldname: 'attribute_name',
			label: (' '),
			fieldtype: 'Data',
			in_list_view: 1,
			read_only: 1,
			columns: 1
		});
		for (let i = 0; i < template_data.columns.attribute_abbr.length; i++) {
			variant_fields.push({
				fieldname: template_data.columns.attribute_abbr[i],
				label: template_data.columns.attribute_abbr[i],
				fieldtype: 'Int',
				in_list_view: 1,
				columns: 1
			});
		}
		/*variant_fields.push({
			fieldname: 'total',
			label: __('Total'),
			fieldtype: 'Int',
			in_list_view: 1,
			read_only: 1,
			columns: 1
		});*///Total columnd will be added after initial tests are completed!
		let variant_data = [];
		if (row.variant_data && row.variant_data.length > 0) {
			variant_data = JSON.parse(row.variant_data);
		} else {
			//We need to generate variant data based on template info
			for (let i = 0; i < template_data.rows.attribute_abbr.length; i++) {
				let row_info = {};
				for (let j = 0; j < template_data.columns.attribute_abbr.length; j++) {
					row_info['attribute_name'] = template_data.rows.attribute_abbr[i];
					row_info[template_data.columns.attribute_abbr[j]] = 0
					//row_info['total'] = 0
					row_info['column_attribute_name'] = template_data.columns.attribute_name;
					row_info['row_attribute_name'] = template_data.rows.attribute_name;
				}
				variant_data.push(row_info);
			}
		}
		var dlgVariantSelector = new frappe.ui.Dialog({
			size: "extra-large",
			fields: [
				{ 'fieldname': 'directive', 'fieldtype': 'HTML' },
				{
					fieldname: "variant_data",
					fieldtype: "Table",
					cannot_add_rows: true,
					in_place_edit: true,
					data: variant_data,
					get_data: () => {
						return variant_data;
					},
					fields: variant_fields
				}
			],
			primary_action: function () {
				//Process variant data and create item rows
				frappe.call({
					method: "erpnextturkish.td_utils.process_variant_json_data",
					args: {
						strTemplateItem: row.item_template,
						jsonData: JSON.stringify(dlgVariantSelector.get_values().variant_data)
					},
					callback: (r) => {
						console.log(r);
						if (r.message.op_result === false) {
							frappe.throw(r.message.op_message);
						} else {
							erpnext.utils.remove_empty_first_row(frm, "items");
							//Remove previously added rows from the item grid for the current variant row.
							let dItemGridLength = frm.doc.items.length;
							for (var dIndex = dItemGridLength - 1; dIndex >= 0; dIndex--) {
								if (frm.doc.items[dIndex].custom_ld_variant_grid_row_name === row.name) {
									frm.doc.items.splice(dIndex, 1);
								}
							}
							//Add new variant item rows
							for (var dIndex = 0; dIndex < r.message.variant_item_info.length; dIndex++) {
								//r.message.variant_item_info.forEach((variant) => {
								var variant = r.message.variant_item_info[dIndex];
								var child = frm.add_child("items");
								frappe.model.set_value(child.doctype, child.name, "item_code", variant.item_code);
								frappe.model.set_value(child.doctype, child.name, "qty", variant.qty);
								if(frm.doc.set_warehouse){
									frappe.model.set_value(child.doctype, child.name, "warehouse", frm.doc.set_warehouse);
								}
								frappe.model.set_value(child.doctype, child.name, "custom_ld_variant_grid_row_name", row.name);
							}
							frm.refresh_field("items");
						}
					}
				})

				dlgVariantSelector.hide();
				frappe.model.set_value(cdt, cdn, 'variant_data', JSON.stringify(dlgVariantSelector.get_values().variant_data));
			}
		});
		dlgVariantSelector.fields_dict.directive.$wrapper.html('Ürün Tercihinizi Giriniz');
		dlgVariantSelector.show();
		dlgVariantSelector.fields_dict.variant_data.grid.wrapper.find('.row-check').hide();
	});
}

frappe.ui.form.on("Stock Reconciliation", {
	onload: function(frm) {
		//Check td utils, show_variant_selection_in_sr setting.https://app.asana.com/0/1199512727558833/1206652223240041/f
		frappe.db.get_single_value("TD Utils", "show_variant_selection_in_sr").then( (r) => {
			if (r === 1) {
				frm.toggle_display("custom_ld_variant_selector", true);
			} else {
				frm.toggle_display("custom_ld_variant_selector", false);
			}
		});
	},
	refresh: function (frm) {
		//Show only items with variants
		frm.set_query("item_template", "custom_ld_variant_selector", function (doc) {
			return { "filters": { "has_variants": "1" } }
		});
	}
});

frappe.ui.form.on('TD Variant Selector', {
	select(frm, cdt, cdn) {
		//Show variant selector dialog.https://app.asana.com/0/1199512727558833/1206652223240041/f
		let row = locals[cdt][cdn];
		if (row.item_template) {
			ShowVariantSelectorDialog(frm, cdt, cdn, row);
		} else {
			frappe.msgprint(__("Select a template first!"));
		}
	}
})