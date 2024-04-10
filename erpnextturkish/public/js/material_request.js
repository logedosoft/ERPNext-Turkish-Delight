/* LOGEDOSOFT 2024*/
//Material Request customizations
async function get_template_data(template_item_code) {
	//Will return attributes of the selected item template. (IE possible values)
	return await frappe.call({
		method: "erpnextturkish.td_utils.get_template_attributes",
		args: {
			strTemplateItemCode: template_item_code
		},
		callback: (r) => {
			return r;
		}
	})
}

function ShowVariantSelectorDialog(frm, cdt, cdn) {
	//Shows a dialog about possible values of the selected item template
	let row = locals[cdt][cdn];
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
		variant_fields.push({
			fieldname: 'total',
			label: __('Total'),
			fieldtype: 'Int',
			in_list_view: 1,
			read_only: 1,
			columns: 1
		});
		let variant_data = [];
		for (let i = 0; i < template_data.rows.attribute_abbr.length; i++) {
			let row_info = {};
			for (let j = 0; j < template_data.columns.attribute_abbr.length; j++) {
				row_info['attribute_name'] = template_data.rows.attribute_abbr[i];
				row_info[template_data.columns.attribute_abbr[j]] = 0
				row_info['total'] = 0
			}
			variant_data.push(row_info);
		}
		console.log(variant_fields);
		console.log(variant_data);
		var dlgVariantSelector = new frappe.ui.Dialog({
			size: "extra-large",
			fields: [
				{ 'fieldname': 'ht', 'fieldtype': 'HTML' },
				{ 'fieldname': 'today', 'fieldtype': 'Date', 'default': frappe.datetime.nowdate() },
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
				dlgVariantSelector.hide();
				console.log(dlgVariantSelector.get_values());
			}
		});
		dlgVariantSelector.fields_dict.ht.$wrapper.html('Ürün Tercihinizi Giriniz');
		dlgVariantSelector.show();
		dlgVariantSelector.fields_dict["variant_data"].grid.wrapper.find('.row-check').hide();
	});
}

frappe.ui.form.on("Material Request", {
	onload: function(frm) {
		//Check td utils, show_variant_selection_in_mr setting.https://app.asana.com/0/1199512727558833/1206652223240041/f
		frappe.db.get_single_value("TD Utils", "show_variant_selection_in_mr").then( (r) => {
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
		ShowVariantSelectorDialog(frm, cdt, cdn);
	}
})