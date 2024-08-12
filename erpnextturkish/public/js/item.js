/* LOGEDOSOFT 2024*/
//Item customizations

async function get_template_valid_attributes(template_item_code) {
	//Will return attributes of the selected item template. Returns only attributes with valid items.
	return await frappe.call({
		method: "erpnextturkish.td_utils.get_template_valid_attributes",
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
	});
}

frappe.ui.form.on("Item", {
	onload: function (frm) {
		//Check td utils, show_variant_size_chart_in_template_item setting. https://app.asana.com/0/1199512727558833/1208016876366999/f
		if (frm.doc.has_variants === 1) {	
			frappe.db.get_single_value("TD Utils", "show_variant_size_chart_in_template_item").then((r) => {
				if (r === 1) {
					//Variant Size Chart operations
					let grdVariantChart = frm.get_field("custom_ld_variant_size_chart").grid;

					//TODO:Doesn't work. 
					//grdVariantChart.wrapper.find('.row-check').hide();
					//grdVariantChart.wrapper.find('.row-index').hide();

					get_template_valid_attributes(frm.doc.name).then( (r) => {
						//template_data = template_data.message;
						console.log(r);
						//r.message.attribute_list.sort(); Moved to backend

						let dColumnIndex = 2;
						let dfVariantChart = frappe.meta.docfield_list["TD Variant Size Chart"];
						
						r.message.attribute_list.forEach( (size, d) => {
							let column = dfVariantChart.find(num => num.idx === dColumnIndex);
							column.label = size;
							//Below code works on production, above code works on dev :)
							let dfAttribute = frappe.meta.get_docfield("TD Variant Size Chart", column.fieldname, frm.doc.name);
							dfAttribute.label = size;
							

							dColumnIndex += 1;
						});
						//Remove columns on right
						dColumnIndex -= 2;
						dfVariantChart.forEach( (column, d) => {
							if (d > dColumnIndex) {
								grdVariantChart.toggle_display(column.fieldname, false);
							}
						});

						grdVariantChart.reset_grid();
						frm.toggle_display("custom_ld_variant_size_chart", true);
					});

				} else {
					frm.toggle_display("custom_ld_variant_size_chart", false);
				}
			});
		} else {
			frm.toggle_display("custom_ld_variant_size_chart", false);
		}
	},
	refresh: function (frm) {
		
	}
});