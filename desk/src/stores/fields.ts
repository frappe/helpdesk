import { defineStore } from "pinia";
import { call } from "frappe-ui";
import { Field } from "@/types";
import { useError } from "@/composables/error";

export const useFieldsStore = defineStore("fields", () => {
  const storage = new Map<string, Array<Field>>();

  /**
   * Fetches the fields for a given `DocType`. Uses an API, hence the async.
   * This includes custom fields as well. Fetching from `DocType` JSON is another option.
   * But it doesn't include custom fields. This logic could be revisited later.
   */
  async function fetch(doctype: string) {
    if (storage.has(doctype)) return;
    const args = {
      doctype,
    };
    await call("helpdesk.api.doc.get_filterable_fields", args)
      .then((data) => storage.set(doctype, data))
      .catch(useError());
  }

  /**
   * Returns the fields for a given `DocType`. If not found, returns an empty array.
   * Use `fetch` to fetch the fields first.
   */
  function get(doctype: string) {
    return storage.get(doctype) || [];
  }

  return {
    fetch,
    get,
  };
});
