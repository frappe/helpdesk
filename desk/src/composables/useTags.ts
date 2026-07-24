import { call, createListResource } from "frappe-ui";
import { toValue, type MaybeRefOrGetter } from "vue";

export interface Tag {
  name: string;
  color?: string;
}

/**
 * Tag CRUD for a single document. `tagListResource` is the shared master list
 * of helpdesk tags. `add` routes through the document's own `add_tag` method,
 * which creates the helpdesk Tag (with colour) if missing and links it in a
 * single call; `remove` unlinks via the core endpoint. The doctype must expose
 * an `add_tag(label, color)` whitelisted method (HD Ticket does).
 */
export function useTags(doctype: string, docname: MaybeRefOrGetter<string>) {
  const tagListResource = createListResource({
    doctype: "Tag",
    fields: ["name", "color"],
    cache: ["Tags", "Helpdesk"],
    filters: { app: "helpdesk" },
    orderBy: "name asc",
    pageLength: 500,
    auto: true,
  });

  function add(label: string, color = "Gray") {
    return call("run_doc_method", {
      dt: doctype,
      dn: toValue(docname),
      method: "add_tag",
      args: { label, color },
    });
  }

  function remove(tag: string) {
    return call("frappe.desk.doctype.tag.tag.remove_tag", {
      tag,
      dt: doctype,
      dn: toValue(docname),
    });
  }

  return { tagListResource, add, remove };
}
