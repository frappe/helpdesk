import { frappeRequest } from "frappe-ui";

// These endpoints are GET-only; frappe-ui's `call` sends POST.
export const getDocs = (method: string, params = {}) =>
  frappeRequest({ url: `helpdesk.api.docs_source.${method}`, method: "GET", params });
