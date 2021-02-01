//Purchase Order Customizations
frappe.ui.form.on("Purchase Order", {
	onload_post_render: (frm) => {
        //Forma dosya guncelle butonunu ekleyelim
        frm.add_custom_button(
            __('Dosya Eklerini Güncelle'),
			function() {
                console.log("Dosya Eklerini Güncelle started");
				frappe.call({
					method:"erpnextturkish.td_utils.td_attach_all_docs_from_item",
					args:{ document:frm.doc, strURL:location.origin, },
					callback: function(r) {
						frm.reload_doc();
                    }
                });
                console.log("Dosya Eklerini Güncelle finished");
            }, 
            __("Tools")
        );
    }
});