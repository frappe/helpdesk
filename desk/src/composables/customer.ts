import { __ } from "@/translation";
import { DocumentResource } from "@/types";
import { HDCustomer } from "@/types/doctypes";
import { createDocumentResource } from "frappe-ui";
import { computed, h, markRaw, reactive, watch } from "vue";
import LucideGlobe from "~icons/lucide/globe";
import LucideMapPin from "~icons/lucide/map-pin";
import LucideUser from "~icons/lucide/user";
import LucideUsers from "~icons/lucide/users";
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
        state.customerType = data.customer_type || "Company";
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
      state.country !== (doc.doc?.country || "") ||
      state.customerType !== (doc.doc?.customer_type || "Company")
    );
  });
  const hasNameChanged = computed(() => state.name !== doc.doc?.customer_name);
  const isDirty = computed(() => {
    return isCustomerInfoChanged.value || hasNameChanged.value || false;
  });

  function findCustomerDoc(): DocumentResource<HDCustomer> {
    const key = name as string;
    const cached = customerCache[key];
    if (cached) return cached;
    else {
      const newDoc = createDocumentResource({
        doctype: "HD Customer",
        name: name,
        whitelistedMethods: {
          getContacts: "get_contacts",
          addContacts: "add_contacts",
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
    customerType: "Company",
    domain: "",
    image: "",
    country: "",
  });
}

function usePrimaryContactState() {
  return reactive<Record<PrimaryContactKey, string>>({
    firstName: "",
    lastName: "",
    email: "",
    mobileNo: "",
  });
}

/** Bundles the customer + primary-contact state for the New Customer dialog. */
export function useNewCustomerForm() {
  const state = useCustomerState();
  const primaryContact = usePrimaryContactState();
  applyDefaults();

  function reset() {
    Object.assign(state, useCustomerState());
    Object.assign(primaryContact, usePrimaryContactState());
    applyDefaults();
  }

  function applyDefaults() {
    state.country = window.default_country || "";
  }

  return { state, primaryContact, reset };
}

type StateKey = "name" | "customerType" | "domain" | "image" | "country";

type PrimaryContactKey = "firstName" | "lastName" | "email" | "mobileNo";

interface FieldConfig {
  key: StateKey;
  type: "text" | "select" | "textarea" | "checkbox" | "autocomplete" | "Link";
  label: string;
  required?: boolean;
  placeholder?: string;
  description?: string;
  prefix?: ReturnType<typeof markRaw> | ReturnType<typeof h>;
  doctype?: string; // only for Link type
  options?: SelectOption[]; // only for select type
}

interface SelectOption {
  label: string;
  value: string;
  icon?: ReturnType<typeof markRaw> | ReturnType<typeof h>;
}
export const customerFields: FieldConfig[] = [
  {
    key: "name",
    type: "text",
    label: __("Name"),
    required: true,
  },
  {
    key: "customerType",
    type: "select",
    label: __("Customer Type"),
    options: [
      {
        label: __("Company"),
        value: "Company",
        icon: markRaw(OrganizationsIcon),
      },
      {
        label: __("Individual"),
        value: "Individual",
        icon: markRaw(LucideUser),
      },
      {
        label: __("Partnership"),
        value: "Partnership",
        icon: markRaw(LucideUsers),
      },
    ],
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
