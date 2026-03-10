import { __ } from "@/translation";
import { DocumentResource } from "@/types";
import { HDCustomer } from "@/types/doctypes";
import { createDocumentResource } from "frappe-ui";
import { h, markRaw, reactive, watch } from "vue";
import LucideGlobe from "~icons/lucide/globe";
import LucideMapPin from "~icons/lucide/map-pin";
import { OrganizationsIcon } from "../components/icons";

type StateKey = "name" | "domain" | "image" | "country";

interface FieldConfig {
  key: StateKey;
  type: "text" | "select" | "textarea" | "checkbox" | "autocomplete" | "Link";
  label: string;
  required?: boolean;
  placeholder?: string;
  description?: string;
  prefix?: ReturnType<typeof markRaw> | ReturnType<typeof h>;
  doctype?: string; // only for Link type
}

export const customerFields: FieldConfig[] = [
  {
    key: "name",
    type: "text",
    label: __("Name"),
    required: true,
    prefix: markRaw(OrganizationsIcon),
  },
  {
    key: "country",
    type: "Link",
    label: __("Country"),
    placeholder: __("Select Country"),
    prefix: h(LucideMapPin, { class: "size-4 mr-1.5" }),
    doctype: "Country",
  },
  {
    key: "domain",
    type: "text",
    label: __("Domain"),
    placeholder: "frappe.io",
    description: __(
      "Domain of the customer, eg: tesla.com. This will be used to auto-assign tickets to this customer based on the sender's email domain."
    ),
    prefix: h(LucideGlobe, { class: "size-4" }),
  },
];

export const useCustomer = (
  name: string | null = null,
  existingDoc: DocumentResource<HDCustomer> | null = null
) => {
  const doc: DocumentResource<HDCustomer> = existingDoc
    ? existingDoc
    : createDocumentResource({
        doctype: "HD Customer",
        name: name,
        whitelistedMethods: {
          getContacts: "get_contacts",
          updateContacts: "update_contacts",
          getPendingInvites: "get_pending_invites",
        },
      });

  const state = reactive<Record<StateKey, string>>({
    name: name ? name : "",
    domain: "",
    image: "",
    country: "",
  });

  if (name || existingDoc) {
    watch(
      () => doc.doc,
      (data) => {
        if (data) {
          state.name = data.customer_name || "";
          state.domain = data.domain || "";
          state.image = data.image || "";
          state.country = data.country || "";
        }
      },
      { immediate: true }
    );
  }
  function isDirty() {
    return (
      state.name !== doc.doc?.customer_name ||
      state.domain !== doc.doc?.domain ||
      state.image !== doc.doc?.image ||
      state.country !== doc.doc?.country
    );
  }

  return {
    doc,
    state,
    isDirty,
  };
};
