import { __ } from "@/translation";
import { DocumentResource } from "@/types";
import { HDCustomer } from "@/types/doctypes";
import { createDocumentResource } from "frappe-ui";
import { computed, h, markRaw, reactive, watch } from "vue";
import LucideGlobe from "~icons/lucide/globe";
import LucideMapPin from "~icons/lucide/map-pin";
import { OrganizationsIcon } from "../components/icons";

const customerCache: Record<string, DocumentResource<HDCustomer>> = {};

export function useCustomer(name: string) {
  const state = useCustomerState(name);
  const doc = findCustomerDoc();

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

  const isCustomerInfoChanged = computed(() => {
    return (
      state.domain !== (doc.doc?.domain || "") ||
      state.image !== (doc.doc?.image || "") ||
      state.country !== (doc.doc?.country || "")
    );
  });
  const hasNameChanged = computed(() => state.name !== doc.doc?.customer_name);
  const isDirty = computed(() => {
    return isCustomerInfoChanged.value || hasNameChanged.value || false;
  });

  function findCustomerDoc(): DocumentResource<HDCustomer> {
    const key = name as string;
    if (customerCache.hasOwnProperty(key)) return customerCache[key];
    else {
      const newDoc = createDocumentResource({
        doctype: "HD Customer",
        name: name,
        whitelistedMethods: {
          getContacts: "get_contacts",
          updateContacts: "update_contacts",
          getPendingInvites: "get_pending_invites",
        },
      });
      customerCache[key] = newDoc;
      return newDoc;
    }
  }

  return {
    doc,
    state,
    isCustomerInfoChanged,
    hasNameChanged,
    isDirty,
  };
}
export function useCustomerState(name?: string | null) {
  return reactive<Record<StateKey, string>>({
    name: name ? name : "",
    domain: "",
    image: "",
    country: "",
  });
}

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
    prefix: h(LucideGlobe, { class: "size-4" }),
  },
];
