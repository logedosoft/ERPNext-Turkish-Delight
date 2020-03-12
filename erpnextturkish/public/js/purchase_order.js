//Purchase Order Customizations
frappe.ui.form.on("Purchase Order", {
	onload_post_render: (frm) => {
        //Forma dosya guncelle butonunu ekleyelim
        frm.add_custom_button(
            __('Dosya Eklerini Güncelle'),
			function() {
				frappe.call({
					method:"erpnextturkish.td_utils.attach_all_docs",
					args:{ document:frm.doc, strURL:location.origin, },
					callback: function(r) {
						frm.reload_doc();
					}
				});
            }//, 
            //__("Tools")
        );
    }
});