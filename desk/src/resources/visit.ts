import { createResource } from "frappe-ui";
import { useError } from "@/composables";

/**
 * Track visit to a document. This is a Frappe resource, which can
 * be called using `.submit({ dt, dn })`
 * */
export const trackVisit = createResource({
  url: "helpdesk.helpdesk.doctype.hd_visit.hd_visit.track_visit",
  auto: false,
  onError: useError(),
});
