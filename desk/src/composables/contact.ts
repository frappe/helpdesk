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

let entryKeyCounter = 0;
export const nextEntryKey = () => ++entryKeyCounter;

function sortByPrimary<T extends { isPrimary: boolean }>(arr: T[]): T[] {
  return [...arr].sort((a, b) => Number(b.isPrimary) - Number(a.isPrimary));
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
    }
  }
  watch(
    () => doc.doc,
    (data) => {
      if (!data) return;
      state.firstName = data.first_name || "";
      state.lastName = data.last_name || "";
      state.image = data.image || "";
      state.emails = sortByPrimary(
        data.email_ids?.map((e: any) => ({
          email_id: e.email_id,
          isPrimary: Boolean(e.is_primary),
          key: nextEntryKey(),
        })) || []
      );
      state.phones = sortByPrimary(
        data.phone_nos?.map((p: any) => ({
          phone: p.phone,
          isPrimary: Boolean(p.is_primary_phone || p.is_primary_mobile_no),
          key: nextEntryKey(),
        })) || []
      );
      state.customers =
        data.links?.map((l: any) => l.link_name as string) || [];
    },
    { immediate: true }
  );

  watch(
    () => contactInfoResource.data,
    (data) => {
      state.timezone = { value: data?.timezone, label: data?.timezone };
    },
    { immediate: true, deep: true }
  );

  const isContactInfoChanged = computed(() => {
    return (
      state.firstName !== (doc.doc?.first_name || "") ||
      state.image !== (doc.doc?.image || "")
    );
  });

  const isDirty = computed(() => {
    const currentEmails = sortByPrimary(
      state.emails.map((e) => ({
        email_id: e.email_id,
        isPrimary: e.isPrimary,
      }))
    );
    const savedEmails = sortByPrimary(
      doc.doc?.email_ids?.map((e: any) => ({
        email_id: e.email_id,
        isPrimary: Boolean(e.is_primary),
      })) || []
    );
    const currentPhones = sortByPrimary(
      state.phones
        .filter((p) => p.phone)
        .map((p) => ({
          phone: p.phone,
          isPrimary: p.isPrimary,
        }))
    );
    const savedPhones = sortByPrimary(
      doc.doc?.phone_nos?.map((p: any) => ({
        phone: p.phone,
        isPrimary: Boolean(p.is_primary_phone || p.is_primary_mobile_no),
      })) || []
    );
    const currentTimezone =
      typeof state.timezone === "string"
        ? state.timezone
        : (state.timezone as any)?.value || "";
    const savedTimezone = contactInfoResource.data?.timezone || "";
    return (
      state.firstName !== (doc.doc?.first_name || "") ||
      state.lastName !== (doc.doc?.last_name || "") ||
      state.image !== (doc.doc?.image || "") ||
      currentTimezone !== savedTimezone ||
      JSON.stringify(currentEmails) !== JSON.stringify(savedEmails) ||
      JSON.stringify(currentPhones) !== JSON.stringify(savedPhones)
    );
  });

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
      timezone:
        typeof state.timezone === "string"
          ? state.timezone
          : state.timezone?.value || "",
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
          throw new Error(__(`Invalid email address: ${e.email_id}`));
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

  return {
    doc,
    contactInfoResource,
    state,
    resetState,
    isContactInfoChanged,
    isDirty,
    parseContactData,
    editContactResource,
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
        state.invite
          ? __("Contact created and invited")
          : __("Contact created")
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
      timezone:
        typeof state.timezone === "string"
          ? state.timezone
          : state.timezone?.value || "",
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
      invite: false,
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
      timezone: "",
    });

    function resetState() {
      const data = doc?.doc;
      state.firstName = data?.first_name || "";
      state.lastName = data?.last_name || "";
      state.image = data?.image || "";
      state.emails = sortByPrimary(
        data?.email_ids?.map((e: any) => ({
          email_id: e.email_id,
          isPrimary: Boolean(e.is_primary),
          key: nextEntryKey(),
        })) || []
      );
      state.phones = sortByPrimary(
        data?.phone_nos?.map((p: any) => ({
          phone: p.phone,
          isPrimary: Boolean(p.is_primary_phone || p.is_primary_mobile_no),
          key: nextEntryKey(),
        })) || []
      );
      state.customers =
        data?.links?.map((l: any) => l.link_name as string) || [];
      state.timezone = data?.timezone || "";
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
    transform: (data) => {
      const template = data[0];
      if (!template) return data;
      template['feedback_extra'] = "";

      const demoFeedback = [
        {
          subject: "Account Recovery Request",
          feedback_rating: 0.8,
          feedback: "Problem Solved Quickly",
          feedback_extra:
            "The response time was a bit longer than anticipated, especially for a simple request involving just one file. A faster turnaround in these situations would greatly enhance overall efficiency.",
        },
        {
          subject: "Unable to log in to dashboard",
          feedback_rating: 1,
          feedback: "Excellent Support",
          feedback_extra:
            "The agent walked me through every step patiently and had my access restored within minutes. Truly impressed with the professionalism.",
        },
        {
          subject: "Billing discrepancy on latest invoice",
          feedback_rating: 1,
          feedback: "Issue Resolved on First Contact",
          feedback_extra:
            "My refund was processed the same day and the breakdown was explained clearly. No back and forth needed at all.",
        },
        {
          subject: "Feature request: dark mode export",
          feedback_rating: 0.6,
          feedback: "Helpful but Slow",
          feedback_extra:
            "The support was friendly and knowledgeable, though it took a couple of follow-ups before I got a definitive answer.",
        },
        {
          subject: "Integration webhook not firing",
          feedback_rating: 0.8,
          feedback: "Knowledgeable Agent",
          feedback_extra:
            "Clear technical explanation and a working fix. Would have loved a short summary of the root cause for my records.",
        },
        {
          subject: "Data export stuck in processing",
          feedback_rating: 0.4,
          feedback: "Took Longer Than Expected",
          feedback_extra:
            "The issue was eventually fixed, but it stayed open for almost three days with little communication in between.",
        },
        {
          subject: "Mobile app crashing on startup",
          feedback_rating: 0.2,
          feedback: "Unresolved Issue",
          feedback_extra:
            "I had to explain the problem multiple times and the suggested steps did not work. Still waiting on a real solution.",
        },
        {
          subject: "Password reset email not received",
          feedback_rating: 1,
          feedback: "Fast and Friendly",
          feedback_extra:
            "Got a reply within minutes and the whole thing was sorted before I finished my coffee. Great experience overall.",
        },
        {
          subject: "Permission error on shared folder",
          feedback_rating: 0.6,
          feedback: "Decent Resolution",
          feedback_extra:
            "The access issue was fixed, but I wish the agent had confirmed everything was working before closing the ticket.",
        },
        {
          subject: "API rate limit reached unexpectedly",
          feedback_rating: 0.4,
          feedback: "Needs Improvement",
          feedback_extra: "",
        },
      ];

      return demoFeedback.map((entry, i) => ({
        ...template,
        name: `${template.name}-${i}`,
        ...entry,
      }));
    },
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
