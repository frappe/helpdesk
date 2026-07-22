frappe.ui.form.on("HD Customer", {
  refresh: function (frm) {
    frm.set_query("primary_contact", function () {
      return {
        filters: {
          name: [
            "in",
            (frm.doc.contacts || []).map((c) => c.contact_name).filter(Boolean),
          ],
        },
      };
    });
  },
});
