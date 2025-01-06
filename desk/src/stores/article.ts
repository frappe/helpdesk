import { createResource } from "frappe-ui";

export const newArticle = createResource({
  url: "frappe.client.insert",
  makeParams({ title, content }) {
    return {
      doc: {
        doctype: "HD Article",
        title,
        content,
      },
    };
  },
  validate({ doc }) {
    if (!doc.title) throw "Title is required";
    if (!doc.content) throw "Content is required";
  },
});

export const updateArticle = createResource({
  url: "frappe.client.set_value",
});

export const deleteArticle = createResource({
  url: "frappe.client.delete",
});
