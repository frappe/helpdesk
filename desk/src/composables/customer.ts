import { __ } from "@/translation";
import { DocumentResource, Error } from "@/types";
import { HDCustomer } from "@/types/doctypes";
import { getErrorMessage, validateEmailWithZod } from "@/utils";
import { useDebounceFn } from "@vueuse/core";
import { call, createDocumentResource } from "frappe-ui";
import { computed, h, markRaw, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";
import LucideGlobe from "~icons/lucide/globe";
import LucideMapPin from "~icons/lucide/map-pin";
import LucideUser from "~icons/lucide/user";
import LucideUsers from "~icons/lucide/users";
import { OrganizationsIcon } from "../components/icons";

const customerCache: Record<string, DocumentResource<HDCustomer>> = {};

export function useCustomer(name: string) {
  const router = useRouter();
  const state = useCustomerState(name);
  const doc = findCustomerDoc();

  async function handleDelete({
    deleteLinkedTickets,
  }: {
    deleteLinkedTickets: boolean;
  }) {
    try {
      await call("helpdesk.api.customer.delete_customer", {
        name,
        delete_tickets: deleteLinkedTickets,
      });
      router.push({ name: "CustomerList" });
    } catch (err) {
      getErrorMessage(err as Error, true);
      throw err;
    }
  }

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
    handleDelete,
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

interface ExistingContact {
  name: string;
  first_name?: string;
  last_name?: string;
  mobile_no?: string;
  phone?: string;
  image?: string;
}

/** Bundles the customer + primary-contact state for the New Customer dialog. */
export function useNewCustomerForm() {
  const state = useCustomerState();
  const primaryContact = usePrimaryContactState();
  const existingContact = ref<ExistingContact | null>(null);
  applyDefaults();

  const existingContactName = computed(() => {
    const contact = existingContact.value;
    if (!contact) return "";
    const fullName = [contact.first_name, contact.last_name]
      .filter(Boolean)
      .join(" ");
    return fullName || contact.name;
  });

  const lookupContact = useDebounceFn(async (email: string) => {
    const contact = validateEmailWithZod(email)
      ? await fetchContactByEmail(email)
      : null;
    if (email !== primaryContact.email) return;
    existingContact.value = contact?.name ? contact : null;
  }, 300);

  function dismissExistingContact() {
    existingContact.value = null;
    primaryContact.email = "";
  }

  function reset() {
    existingContact.value = null;
    Object.assign(state, useCustomerState());
    Object.assign(primaryContact, usePrimaryContactState());
    applyDefaults();
  }

  function applyDefaults() {
    state.country = window.default_country || "";
  }

  watch(() => primaryContact.email, lookupContact);

  return {
    state,
    primaryContact,
    existingContact,
    existingContactName,
    dismissExistingContact,
    reset,
  };
}

function fetchContactByEmail(email: string): Promise<ExistingContact | null> {
  return call("frappe.client.get_value", {
    doctype: "Contact",
    filters: { email_id: email },
    fieldname: ["name", "first_name", "last_name", "mobile_no", "phone", "image"],
  });
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
export const customerTypeOptions: SelectOption[] = [
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
];

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
    options: customerTypeOptions,
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
