// Copyright (c) 2023, Frappe Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("HD Ticket", {
	refresh(frm) {
        var idx = 1; // Initialize index counter

        // Sort the time_tracking_table array of objects based on start_time attribute
        frm.doc.time_tracking_table.sort(function(a,b){
        if (a.start_time < b.start_time){ // If start_time of 'a' is less than start_time of 'b'
            return -1 // Place 'a' before 'b'
        }
        else if (a.start_time > b.start_time){ // If start_time of 'a' is greater than start_time of 'b'
            return 1 // Place 'b' before 'a'
        }
        return 1; // Keep the order unchanged (considering it's ascending)
        });

        // Map through each item in the sorted time_tracking_table and assign an index
        frm.doc.time_tracking_table.map(function(item){
            item.idx = idx++; // Assigning incremental index
        });

        frm.refresh_field("time_tracking_table");
    },
});
