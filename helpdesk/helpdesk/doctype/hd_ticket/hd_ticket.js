// Copyright (c) 2023, Frappe Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("HD Ticket", {
  onload(frm) {
    if (frm.is_new()) return;
    frm.call("mark_seen");
    apply_itil_mode(frm);
    // Apply cascading filter for sub_category if category already set (AC #4)
    apply_sub_category_filter(frm);
  },

  refresh(frm) {
    apply_itil_mode(frm);
    // Re-apply cascading filter on refresh for existing tickets (AC #4)
    apply_sub_category_filter(frm);
  },

  impact(frm) {
    update_priority_read_only(frm);
  },

  urgency(frm) {
    update_priority_read_only(frm);
  },

  // Cascading filter: when category changes, filter sub_category (AC #4, #5)
  category(frm) {
    apply_sub_category_filter(frm);
    // Clear sub_category when category is cleared (AC #4)
    if (!frm.doc.category) {
      frm.set_value("sub_category", "");
    }
    frm.refresh_field("sub_category");
  },

  // Set up query for sub_county to filter by county
  county(frm) {
    if (!frm.doc.county) {
      frm.set_value("sub_county", "");
    }
    frm.refresh_field("sub_county");
  },

  setup(frm) {
    // Set query for sub_county field
    frm.set_query("sub_county", function() {
      if (frm.doc.county) {
        return {
          query: "helpdesk.utils.queries.get_subcounties_by_county",
          filters: {
            county: frm.doc.county
          }
        };
      }
      return {};
    });
  },
});

function apply_itil_mode(frm) {
  frappe.db.get_single_value("HD Settings", "itil_mode_enabled").then((itil_mode_enabled) => {
    // Only impact and urgency are gated behind ITIL mode (AC #3 — category/sub_category
    // are visible in both Simple and ITIL modes for routing and reporting purposes).
    const itil_only_fields = ["impact", "urgency"];

    if (itil_mode_enabled) {
      // ITIL Mode: show impact and urgency fields
      itil_only_fields.forEach((field) => {
        frm.set_df_property(field, "hidden", 0);
      });
      // Priority is read-only when both impact and urgency are set (AC #3, #6)
      update_priority_read_only(frm);
    } else {
      // Simple Mode: hide only impact/urgency; category/sub_category remain visible
      itil_only_fields.forEach((field) => {
        frm.set_df_property(field, "hidden", 1);
      });
      frm.set_df_property("priority", "read_only", 0);
    }

    frm.refresh_fields(["priority", ...itil_only_fields]);
  });
}

/**
 * Make priority read-only when ITIL matrix applies (both impact AND urgency are set).
 * Legacy tickets with empty impact/urgency retain editable priority (AC #6).
 */
function update_priority_read_only(frm) {
  const matrix_active = frm.doc.impact && frm.doc.urgency;
  frm.set_df_property("priority", "read_only", matrix_active ? 1 : 0);
  frm.refresh_field("priority");
}

/**
 * Apply cascading sub_category filter based on currently selected category (AC #4, #5).
 * When category is set, sub_category only shows children of that category.
 * When category is cleared, sub_category filter is removed and value is cleared.
 */
function apply_sub_category_filter(frm) {
  if (frm.doc.category) {
    frm.set_query("sub_category", function () {
      return {
        filters: { parent_category: frm.doc.category },
      };
    });
  } else {
    // No category selected — remove the filter
    frm.set_query("sub_category", function () {
      return {};
    });
  }
}
