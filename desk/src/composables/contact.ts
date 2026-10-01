import { __ } from "@/translation";
import type {
  DocumentResource,
  EditContactState,
  Error,
  ListResource,
  NewContactState,
  Resource,
} from "@/types";
import { Contact, HDTicket } from "@/types/doctypes";
import { getErrorMessage, validateEmailWithZod } from "@/utils";
import {
  call,
  createDocumentResource,
  createListResource,
  createResource,
  toast,
} from "frappe-ui";
import { useOnboarding } from "frappe-ui/frappe";
import { computed, ComputedRef, h, markRaw, reactive, ref, watch } from "vue";
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
  | "phone_nos"
  | "timezone";

type AutocompleteOption = string;

type ContactInfoResource = ReturnType<typeof createResource>;

interface ContactBundle {
  doc: DocumentResource<Contact>;
  info: ContactInfoResource;
}

// Local Cache to store contact document + info resources to avoid multiple DB calls in a single session.
const contactCache: Record<string, ContactBundle> = {};

function sortByPrimary<T extends { isPrimary: boolean }>(arr: T[]): T[] {
  return [...arr].sort((a, b) => Number(b.isPrimary) - Number(a.isPrimary));
}

type EmailRow = { email_id: string; isPrimary: boolean };
type PhoneRow = { phone: string; isPrimary: boolean };

// The single mapping from a Contact document to form-state rows. Kept in one
// place so the hydrate watch, resetState, and the dirty check can never drift.
function emailRowsFromDoc(doc?: Contact): EmailRow[] {
  return sortByPrimary(
    (doc?.email_ids || []).map((e: any) => ({
      email_id: e.email_id,
      isPrimary: Boolean(e.is_primary),
    }))
  );
}

function phoneRowsFromDoc(doc?: Contact): PhoneRow[] {
  return sortByPrimary(
    (doc?.phone_nos || []).map((p: any) => ({
      phone: p.phone,
      isPrimary: Boolean(p.is_primary_phone || p.is_primary_mobile_no),
    }))
  );
}

function customerLinksFromDoc(doc?: Contact): string[] {
  return (doc?.links || []).map((l: any) => l.link_name as string);
}

let entryKeyCounter = 0;
export const nextEntryKey = () => ++entryKeyCounter;

const withKeys = <T>(rows: T[]) =>
  rows.map((row) => ({ ...row, key: nextEntryKey() }));

// Hydrate the edit-form state from a Contact document.
function applyDocToState(state: EditContactState, doc?: Contact): void {
  state.firstName = doc?.first_name || "";
  state.lastName = doc?.last_name || "";
  state.image = doc?.image || "";
  state.emails = withKeys(emailRowsFromDoc(doc));
  state.phones = withKeys(phoneRowsFromDoc(doc));
  state.customers = customerLinksFromDoc(doc);
}

export function useContact(name: string) {
  const router = useRouter();
  const { doc, info: contactInfoResource } = findContact();
  const { state, resetState } = useContactState(false, doc);

  async function handleDelete({
    deleteLinkedTickets,
  }: {
    deleteLinkedTickets: boolean;
  }) {
    try {
      await call("helpdesk.api.contact.delete_contact", {
        name,
        delete_tickets: deleteLinkedTickets,
      });
      router.push({ name: "ContactList" });
    } catch (err) {
      getErrorMessage(err as Error, true);
      throw err;
    }
  }
  watch(
    () => doc.doc,
    (data) => {
      if (!data) return;
      applyDocToState(state, data);
    },
    { immediate: true }
  );

  watch(
    () => contactInfoResource.data,
    (data) => {
      state.timezone = data?.timezone || "";
    },
    { immediate: true, deep: true }
  );

  const isContactInfoChanged = computed(() => {
    return (
      state.firstName !== (doc.doc?.first_name || "") ||
      state.image !== (doc.doc?.image || "")
    );
  });

  const isContactDirty = computed(() => {
    const currentEmails = sortByPrimary(
      state.emails.map((e) => ({
        email_id: e.email_id,
        isPrimary: e.isPrimary,
      }))
    );
    const currentPhones = sortByPrimary(
      state.phones
        .filter((p) => p.phone)
        .map((p) => ({ phone: p.phone, isPrimary: p.isPrimary }))
    );
    const savedTimezone = contactInfoResource.data?.timezone || "";
    return (
      state.firstName !== (doc.doc?.first_name || "") ||
      state.lastName !== (doc.doc?.last_name || "") ||
      state.image !== (doc.doc?.image || "") ||
      state.timezone !== savedTimezone ||
      JSON.stringify(currentEmails) !==
        JSON.stringify(emailRowsFromDoc(doc.doc)) ||
      JSON.stringify(currentPhones) !==
        JSON.stringify(phoneRowsFromDoc(doc.doc))
    );
  });

  // Selecting a customer to link counts as an unsaved change too.
  const isDirty = computed(
    () => isContactDirty.value || Boolean(state.customer)
  );

  function findContact(): ContactBundle {
    if (contactCache.hasOwnProperty(name)) return contactCache[name];
    const bundle: ContactBundle = {
      doc: createDocumentResource({ doctype: "Contact", name }),
      info: createResource({
        url: "helpdesk.api.contact.get_contact_info",
        method: "GET",
        params: { name },
        auto: true,
      }),
    };
    contactCache[name] = bundle;
    return bundle;
  }

  function parseContactData() {
    return {
      first_name: state.firstName,
      last_name: state.lastName,
      image: state.image,
      email_ids: state.emails
        .filter((e) => e.email_id)
        .map((e) => ({
          email_id: e.email_id,
          is_primary: e.isPrimary,
        })),
      phone_nos: state.phones
        .filter((p) => p.phone)
        .map((p) => ({
          phone: p.phone,
          is_primary: p.isPrimary,
        })),
      timezone: state.timezone,
    };
  }

  const editContactResource = createResource({
    url: "helpdesk.api.contact.edit_contact",
    method: "POST",
    validate(data: { name: string; doc: ReturnType<typeof parseContactData> }) {
      if (!data.doc.first_name?.trim()) {
        throw new Error(__("First name is required"));
      }
      if (!data.doc.email_ids.length) {
        throw new Error(__("At least one email address is required"));
      }
      for (const e of data.doc.email_ids) {
        if (!validateEmailWithZod(e.email_id)) {
          throw new Error(__("Invalid email address: {0}", [e.email_id]));
        }
      }
      if (!data.doc.email_ids.some((e) => e.is_primary)) {
        throw new Error(
          __("At least one email address must be marked as primary")
        );
      }
    },
    onSuccess() {
      resetState();
      toast.success(__("Contact updated"));
    },
  });

  // Links this contact to the selected customer
  const linkCustomerResource = createResource({
    url: "run_doc_method",
    makeParams: () => ({
      dt: "HD Customer",
      dn: state.customer,
      method: "add_contacts",
      args: { contacts: JSON.stringify([name]), role: "HD Customer" },
    }),
  });

  return {
    doc,
    contactInfoResource,
    state,
    resetState,
    isContactInfoChanged,
    isContactDirty,
    isDirty,
    parseContactData,
    editContactResource,
    linkCustomerResource,
    handleDelete,
  };
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
    onSuccess: (name: string) => {
      router.push({ name: "Contact", params: { id: name } });
      toast.success(
        state.invite ? __("Contact created and invited") : __("Contact created")
      );
      resetState();
    },
    onError: (err: unknown) => {
      getErrorMessage(err as Error, true);
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
      timezone: state.timezone,
    };
  }

  function addContact() {
    return addContactResource.submit({
      doc: parseContactData(),
      invite: state.invite,
    });
  }

  return {
    state,
    fieldConfig,
    addContact,
    isLoading: computed(() => addContactResource.loading),
    reset: resetState,
  };
}

// Function overloads to provide conditonal types for new vs existing contact states.
export function useContactState(newDoc: true): {
  state: NewContactState;
  resetState: () => void;
};
export function useContactState(
  newDoc: false,
  doc: DocumentResource<Contact>
): {
  state: EditContactState;
  resetState: () => void;
};
export function useContactState(
  newDoc: boolean = false,
  doc?: DocumentResource<Contact>
) {
  if (newDoc) {
    const state = reactive<NewContactState>({
      firstName: "",
      lastName: "",
      image: "",
      email: "",
      phone: "",
      timezone: "",
      customer: "",
      invite: true,
    });

    function resetState() {
      state.firstName = "";
      state.lastName = "";
      state.image = "";
      state.email = "";
      state.phone = "";
      state.timezone = "";
      state.customer = "";
      state.invite = false;
    }

    return { state, resetState };
  } else {
    const state = reactive<EditContactState>({
      firstName: "",
      lastName: "",
      image: "",
      emails: [],
      phones: [],
      customers: [],
      customer: "",
      timezone: "",
    });

    function resetState() {
      const data = doc?.doc;
      applyDocToState(state, data);
      state.timezone = data?.timezone || "";
      state.customer = "";
    }

    return { state, resetState };
  }
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

function getContactFieldConfig(newDoc: boolean = false): FieldConfigRow[] {
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
      key: "customer",
      type: "Link",
      label: __("Customer"),
      placeholder: __("Select Customer"),
      doctype: "HD Customer",
    },
  ];

  return [...baseFields, emailField, phoneField, ...restFields];
}

export function useContactInvite() {
  const isLoading = ref(false);
  // @ts-expect-error
  const { updateOnboardingStep } = useOnboarding("helpdesk");
  async function resendInvite(
    invitationName: string,
    status: string | undefined,
    contactName: string,
    email: string | undefined
  ): Promise<void> {
    if (status === "Expired") {
      return inviteAsUser(contactName, email);
    }
    try {
      isLoading.value = true;
      await call("frappe.core.api.user_invitation.resend_invitation", {
        name: invitationName,
        app_name: "helpdesk",
      });
      toast.success(__("Invitation email resent successfully"));
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
  async function inviteAsUser(
    contactName: string,
    email: string | undefined
  ): Promise<void> {
    if (!email) {
      toast.error(__("Contact has no email address to invite"));
      return;
    }
    try {
      isLoading.value = true;
      await call("frappe.core.api.user_invitation.invite_by_email", {
        emails: email,
        roles: ["HD Customer"],
        redirect_to_path: "/helpdesk",
        app_name: "helpdesk",
        contact: contactName,
      });
      toast.success(__("Invitation sent"));
      updateOnboardingStep("add_invite_contact");
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
  return { resendInvite, inviteAsUser, isLoading };
}

export function useContactResetPassword(getUser: () => string | undefined) {
  const isLoading = ref(false);
  async function resetPassword(): Promise<void> {
    const user = getUser();
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

interface ContactFeedbackChartData {
  average: number;
  total: number;
  data: Record<number, number>;
}

// key of feedback feedbackListResource which has type of ListResource<HDTicket> is feedbackListResource, key of count resource is Resource<number>
interface ContactFeedback {
  feedbackListResource: ListResource<HDTicket>;
  feedbackCount: ReturnType<typeof createResource>;
  chartData: Resource<ContactFeedbackChartData>;
  loading: ComputedRef<boolean>;
}

// Cache to avoid re-creating feedback resources for the same contact in a session
const contactFeedbackCache: Record<string, ContactFeedback> = {};

export function useContactFeedback(name: string): ContactFeedback {
  if (contactFeedbackCache[name]) return contactFeedbackCache[name];

  const feedbackListResource: ListResource<HDTicket> = createListResource({
    doctype: "HD Ticket",
    cache: [name, "FeedbackList"],
    fields: [
      "name",
      "subject",
      "feedback",
      "feedback_rating",
      "feedback_extra",
      "creation",
      "modified",
    ],
    filters: { contact: name, feedback_rating: ["is", "set"] },
    orderBy: "creation desc",
    auto: true,
  });

  const feedbackCount = createResource({
    url: "frappe.client.get_count",
    makeParams: () => ({
      doctype: "HD Ticket",
      filters: {
        contact: name,
        feedback_rating: ["is", "set"],
      },
    }),
    auto: true,
  });

  const chartData = createResource({
    url: "helpdesk.api.ticket_stats.get_feedback_received",
    makeParams: () => ({
      scope: "contact",
      value: name,
    }),
    auto: true,
  });

  const result: ContactFeedback = {
    feedbackListResource,
    feedbackCount,
    chartData,
    loading: computed(
      () =>
        feedbackCount.loading ||
        feedbackListResource.loading ||
        chartData.loading
    ),
  };

  contactFeedbackCache[name] = result;
  return result;
}
