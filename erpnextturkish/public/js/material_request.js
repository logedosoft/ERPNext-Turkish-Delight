/* LOGEDOSOFT 2024*/
//Production Plan customizations
frappe.ui.form.on("Material Request", {
	onload: function(frm) {
		//Check td utils, show_variant_selection_in_mr setting.https://app.asana.com/0/1199512727558833/1206652223240041/f
		frappe.db.get_single_value("TD Utils", "show_variant_selection_in_mr").then( (r) => {
			console.log(r);
			if (r === 1) {
				frm.toggle_display("custom_ld_variant_selector", true);
			} else {
				frm.toggle_display("custom_ld_variant_selector", false);
			}
		});
	}
});