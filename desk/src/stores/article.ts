import { useError } from "@/composables/error";
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
  validate(params) {
    if (!params.doc.title) throw "Title is required";
    if (!params.doc.content) throw "Content is required";
  },
});
