/* LOGEDOSOFT 2024*/
//Production Plan customizations
frappe.ui.form.on("Production Plan", {
	refresh: function(frm) {
		//Check td utils, seperate_wo_and_sco_in_pp setting. 
		//If enabled hide the create->wo/sco button and show 2 additional buttons.
		//https://app.asana.com/0/1199512727558833/1206696674827367/f
		if (frm.doc.docstatus === 1) {
			if (frm.doc.po_items && frm.doc.status !== "Closed") {
				frappe.db.get_single_value("TD Utils", "seperate_wo_and_sco_in_pp").then( (blnWOSCOEnabled)=> {
					console.log(blnWOSCOEnabled);
					if (blnWOSCOEnabled) {
						frm.remove_custom_button("Work Order / Subcontract PO", "Create");
						frm.add_custom_button(__("Work Order"), () => {
							frappe.call({
								method: "erpnextturkish.td_utils.pp_create_wosco",
								freeze: true,
								freeze_message: __("Fox is working on it..."),
								args: {
									'docPP': frm.doc,
									'strType': 'Work Order'
								},
								callback: function () {
									frm.reload_doc();
								}
							});
						}, __('Create'));
						//  Subcontract PO
						frm.add_custom_button(__("Subcontracting Purchase Order"), () => {
							frappe.call({
								method: 'erpnextturkish.td_utils.pp_create_wosco',
								freeze: true,
								freeze_message: __("Fox is working on it..."),
								args: {
									'docPP': frm.doc,
									'strType': 'Subcontracting Order'
								},
								callback: function () {
									frm.reload_doc();
								}
							});
						}, __('Create'));
						frm.page.set_inner_btn_group_as_primary(__('Create'));
					}
				});
			}
		}
	}
})