// One level: a top-level category (is_group) takes Subcategories, a Subcategory none.
frappe.treeview_settings["HD Article Category"] = {
  get_tree_root: false,
  root_label: __("All Categories"),
  add_tree_node:
    "helpdesk.helpdesk.doctype.hd_article_category.hd_article_category.add_node",
  fields: [
    {
      fieldtype: "Data",
      fieldname: "category_name",
      label: __("Name"),
      reqd: 1,
    },
  ],
  get_label: (node) => frappe.utils.escape_html(node.title || node.label),
  onload(treeview) {
    // the categories are many roots: list them under one label
    treeview.root_value = "";
    treeview.make_tree();
  },
  extend_toolbar: true,
  toolbar: [
    {
      label: __("Add Child"),
      icon: "plus",
      condition: (node) =>
        node.expandable && frappe.model.can_create("HD Article Category"),
      click(node) {
        // Frappe's adds under the selected node, not the clicked one
        const treeview = frappe.views.trees["HD Article Category"];
        treeview.tree.set_selected_node(node);
        treeview.new_node();
      },
      btnClass: "hidden-xs",
    },
  ],
};
