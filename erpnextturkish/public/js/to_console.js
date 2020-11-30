$(function() {
	console.log("ON Listing");
	frappe.realtime.on('out_to_console', function(data) {
		data.forEach(element => {
			console.log(element);
		});
	});
});