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

frappe.ui.form.on('HD Ticket Time Tracking', {
    start_time: function(frm, cdt, cdn) {
        var child = locals[cdt][cdn];
        if (!child.end_time) {
            calculate_end_time_based_on_start_and_duration(frm, child);
        } else {
            // If end_time is set, recalculate duration
            calculate_duration_based_on_start_and_end(frm, child);
        }
    },

    end_time: function(frm, cdt, cdn) {
        var child = locals[cdt][cdn];
        // Recalculate duration whenever end_time is changed
        calculate_duration_based_on_start_and_end(frm, child);
    },

    duration: function(frm, cdt, cdn) {
        var child = locals[cdt][cdn];
        // If duration is manually changed and start_time is set, recalculate end_time
        if (child.start_time) {
            calculate_end_time_based_on_start_and_duration(frm, child);
        }
    }
});

function calculate_end_time_based_on_start_and_duration(frm, child) {
    if (child.start_time && child.duration) {
        var start = moment(child.start_time);
        // Use a specific datetime format if frappe.datetime.datetime_format is not working as expected
        var end = start.clone().add(child.duration, 'seconds');
        var formattedEnd = end.format("YYYY-MM-DD HH:mm:ss");

        frappe.model.set_value(child.doctype, child.name, 'end_time', formattedEnd);
    }
}

function calculate_duration_based_on_start_and_end(frm, child) {
    if (child.start_time && child.end_time) {
        var start = moment(child.start_time);
        var end = moment(child.end_time);
        var duration = end.diff(start, 'seconds');
        
        frappe.model.set_value(child.doctype, child.name, 'duration', duration);
    }
}
