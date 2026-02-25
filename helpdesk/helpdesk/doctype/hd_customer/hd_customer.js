// frappe.ui.form.on("HD Customer", {
//   refresh: function (frm) {
//     frm.fields_dict["contacts"].grid.get_field("contact_name").get_query =
//       function () {
//         return {
//           filters: {
//             name: ["not in", frm.doc.contacts.map((c) => c.contact_name)],
//           },
//         };
//       };
//   },
// });
