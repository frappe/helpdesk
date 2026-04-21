import { __ } from "@/translation";
import { DocumentResource, EditContactState, NewContactState } from "@/types";
import { Contact } from "@/types/doctypes";
import { validateEmailWithZod } from "@/utils";
import { call, createDocumentResource, createResource, toast } from "frappe-ui";
import { useOnboarding } from "frappe-ui/frappe";
import { computed, h, markRaw, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";

export type TextInputTypes =
  | "date"
  | "datetime-local"
  | "email"
  | "file"
  | "month"
  | "number"
  | "password"
  | "search"
  | "tel"
  | "text"
  | "time"
  | "url"
  | "week"
  | "range";

type FieldType =
  | TextInputTypes
  | "file"
  | "Link"
  | "autocomplete"
  | "email_ids"
  | "phone_nos";

type AutocompleteOption = string | { label: string; value: string };

// Local Cache to store contact document resources to avoid multiple DB calls in a single session.
const contactCache: Record<string, DocumentResource<Contact>> = {};

export function useContact(name: string) {
  const { state, resetState } = useContactState(false);
  const doc = findContactDoc();

  watch(
    () => doc.doc,
    (data) => {
      if (data) {
        state.firstName = data.first_name || "";
        state.lastName = data.last_name || "";
        state.image = data.image || "";
        state.emails =
          data.email_ids?.map((e: any) => ({
            email_id: e.email_id,
            isPrimary: e.is_primary,
          })) || [];
        state.phones =
          data.phone_nos?.map((p: any) => ({
            phone: p.phone,
            isPrimary: p.is_primary_phone || p.is_primary_mobile_no,
          })) || [];
        state.customers =
          data.links?.map((l: any) => l.link_name as string) || [];
      }
    },
    { immediate: true }
  );

  const isContactInfoChanged = computed(() => {
    return (
      state.firstName !== (doc.doc?.first_name || "") ||
      state.image !== (doc.doc?.image || "")
    );
  });

  const isDirty = computed(() => {
    return isContactInfoChanged.value || false;
  });

  function findContactDoc(): DocumentResource<Contact> {
    const key = name as string;
    if (contactCache.hasOwnProperty(key)) return contactCache[key];
    else {
      const newDoc = createDocumentResource({
        doctype: "Contact",
        name: name,
      });
      contactCache[key] = newDoc;
      return newDoc;
    }
  }

  function parseContactData() {
    return {
      first_name: state.firstName,
      last_name: state.lastName,
      image: state.image,
      email_ids: state.emails.map((e) => ({
        email_id: e.email_id,
        is_primary: e.isPrimary,
      })),
      phone_nos: state.phones.map((p) => ({
        phone: p.phone,
        is_primary_phone: p.isPrimary,
        is_primary_mobile_no: p.isPrimary,
      })),
      links: state.customers.map((name) => ({
        link_doctype: "HD Customer",
        link_name: name,
      })),
    };
  }

  return {
    doc,
    state,
    resetState,
    isContactInfoChanged,
    isDirty,
    parseContactData,
  };
}

// Function overloads to provide conditonal types for new vs existing contact states.
export function useContactState(newDoc: true): {
  state: NewContactState;
  resetState: () => void;
};
export function useContactState(newDoc?: false): {
  state: EditContactState;
  resetState: () => void;
};
export function useContactState(newDoc: boolean = false) {
  if (newDoc) {
    const state = reactive<NewContactState>({
      firstName: "",
      lastName: "",
      image: "",
      email: "",
      phone: "",
      timezone: "",
      customer: "",
    });

    function resetState() {
      state.firstName = "";
      state.lastName = "";
      state.image = "";
      state.email = "";
      state.phone = "";
      state.timezone = "";
      state.customer = "";
    }

    return { state, resetState };
  } else {
    const state = reactive<EditContactState>({
      firstName: "",
      lastName: "",
      image: "",
      emails: [{ email_id: "", isPrimary: true }],
      phones: [{ phone: "", isPrimary: true }],
      customers: [],
      timezone: "",
    });

    function resetState() {
      state.firstName = "";
      state.lastName = "";
      state.image = "";
      state.emails = [{ email_id: "", isPrimary: true }];
      state.phones = [{ phone: "", isPrimary: true }];
      state.customers = [];
      state.timezone = "";
    }

    return { state, resetState };
  }
}

export function useNewContact() {
  const { state, resetState } = useContactState(true);
  const fieldConfig = getContactFieldConfig(true);
  const router = useRouter();

  const addContactResource = createResource({
    url: "helpdesk.api.contact.create_contact",
    method: "POST",
    validate: (data: { doc: ReturnType<typeof parseContactData> }) => {
      if (!data.doc.first_name) {
        throw new Error(__("First name is required"));
      }
      if (!data.doc.email) {
        throw new Error(__("Email address is required"));
      }
      if (!validateEmailWithZod(data.doc.email)) {
        throw new Error(__("Invalid email address"));
      }
    },
  });

  function parseContactData() {
    return {
      first_name: state.firstName,
      last_name: state.lastName,
      image: state.image,
      email: state.email,
      phone: state.phone,
      customer: state.customer,
      timezone:
        typeof state.timezone === "string"
          ? state.timezone
          : state.timezone?.value || "",
    };
  }

  const isLoading = ref(false);
  async function addContact() {
    isLoading.value = true;
    addContactResource.submit(
      { doc: parseContactData() },
      {
        onSuccess: (name: string) => {
          router.push({ name: "Contact", params: { id: name } });
          toast.success(__("Contact created"));
          isLoading.value = false;
          resetState();
        },
      }
    );
  }

  return { state, fieldConfig, addContact, isLoading };
}

interface FieldConfig {
  key: string;
  type: FieldType;
  label: string;
  required?: boolean;
  placeholder?: string;
  description?: string;
  prefix?: ReturnType<typeof markRaw> | ReturnType<typeof h>;
  doctype?: string;
  options?: AutocompleteOption[];
}

type FieldConfigRow = FieldConfig | FieldConfig[];

export function getContactFieldConfig(
  newDoc: boolean = false
): FieldConfigRow[] {
  const baseFields: FieldConfigRow[] = [
    {
      key: "image",
      type: "file",
      label: __("Profile Picture"),
      required: false,
      placeholder: __("Upload profile picture"),
    },
    [
      {
        key: "firstName",
        type: "text",
        label: __("First Name"),
        required: true,
        placeholder: __("John"),
      },
      {
        key: "lastName",
        type: "text",
        label: __("Last Name"),
        placeholder: __("Doe"),
      },
    ],
  ];

  const emailField: FieldConfig = newDoc
    ? {
        key: "email",
        type: "email",
        label: __("Email"),
        required: true,
        placeholder: __("john.doe@example.com"),
      }
    : {
        key: "emails",
        type: "email_ids",
        label: __("Emails"),
      };

  const phoneField: FieldConfig = newDoc
    ? {
        key: "phone",
        type: "tel",
        label: __("Phone"),
        placeholder: __("123-456-7890"),
      }
    : {
        key: "phones",
        type: "phone_nos",
        label: __("Phone Numbers"),
      };

  const restFields: FieldConfigRow[] = [
    {
      key: "timezone",
      type: "autocomplete",
      label: __("Timezone"),
      placeholder: __("Select timezone"),
      options:
        (Intl.supportedValuesOf("timeZone") as AutocompleteOption[]) || [],
    },
    {
      key: "customer",
      type: "Link",
      label: __("Customer"),
      placeholder: __("Select Customer"),
      doctype: "HD Customer",
    },
  ];

  return [...baseFields, emailField, phoneField, ...restFields];
}

export function useContactInvite(doc: DocumentResource<Contact>) {
  const isLoading = ref(false);
  // @ts-expect-error
  const { updateOnboardingStep } = useOnboarding("helpdesk");
  async function inviteContact(): Promise<void> {
    try {
      isLoading.value = true;
      const user = await call(
        "frappe.contacts.doctype.contact.contact.invite_user",
        {
          contact: doc.doc.name,
        }
      );
      toast.success(__("Contact invited successfully"));
      await doc.setValue.submit({
        user: user,
      });
      updateOnboardingStep("add_invite_contact");
    } catch (error: unknown) {
      isLoading.value = false;
      const parser = new DOMParser();
      const doc = parser.parseFromString(
        (error as Error).messages?.[0] || (error as Error).message,
        "text/html"
      );

      const errMsg = doc.body.innerText;
      toast.error(errMsg);
    } finally {
      isLoading.value = false;
    }
  }
  return { inviteContact, isLoading };
}

export function useContactResetPassword(getUser: () => string | undefined) {
  const isLoading = ref(false);
  async function resetPassword(): Promise<void> {
    const user = getUser();
    console.log(user);
    if (!user) {
      toast.error(__("No system user is linked with this contact"));
      return;
    }
    try {
      isLoading.value = true;
      await call("frappe.core.doctype.user.user.reset_password", {
        user,
      });
      toast.success(__("Reset password email sent successfully"));
    } catch (error: unknown) {
      const parser = new DOMParser();
      const doc = parser.parseFromString(
        (error as Error).messages?.[0] || (error as Error).message,
        "text/html"
      );

      const errMsg = doc.body.innerText;
      toast.error(errMsg);
    } finally {
      isLoading.value = false;
    }
  }
  return { resetPassword, isLoading };
}
