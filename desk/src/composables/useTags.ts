import { createResource } from "frappe-ui";

export interface Tag {
  name: string;
  color?: string | null;
}

let tagListResource: ReturnType<typeof createResource> | undefined;

/** Shared master list of helpdesk tags, fetched once. Per-document tag changes
 * go through framework's `update_document_tags` API. */
export function useTags() {
  tagListResource ??= createResource({
    url: "frappe.desk.doctype.tag.tag.get_tags_for_app",
    params: { app: "helpdesk" },
    auto: true,
  });

  return { tagListResource };
}
