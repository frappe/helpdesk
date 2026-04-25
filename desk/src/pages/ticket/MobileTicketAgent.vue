<template>
  <div class="flex flex-col">
    <LayoutHeader v-if="ticket.doc?.name">
      <template #left-header>
        <Breadcrumbs :items="breadcrumbs" />
      </template>
      <template #right-header>
        <div class="absolute right-0 pr-2">
          <Dropdown :options="dropdownOptions">
            <template #default="{ open }">
              <Button :label="ticket.doc.status">
                <template #prefix>
                  <IndicatorIcon
                    :class="
                      ticketStatusStore.getStatus(ticket.doc.status)
                        ?.parsed_color
                    "
                  />
                </template>
                <template #suffix>
                  <FeatherIcon
                    :name="open ? 'chevron-up' : 'chevron-down'"
                    class="h-4"
                  />
                </template>
              </Button>
            </template>
          </Dropdown>
        </div>
      </template>
    </LayoutHeader>
    <header
      class="flex h-12 items-center justify-between py-[7px] px-3 border-b"
      v-if="ticket.doc?.name"
    >
      <!-- left side -->
      <div class="flex items-center gap-2 max-w-[50%]">
        <div v-if="parseAssignees.length">
          <component :is="parseAssignees.length == 1 ? 'Button' : 'div'">
            <MultipleAvatar
              :avatars="parseAssignees"
              @click="showAssignmentModal = true"
            />
          </component>
        </div>
        <button
          v-else
          class="rounded bg-gray-100 px-2 py-1.5 text-base text-gray-800"
          @click="showAssignmentModal = true"
        >
          {{ __("Assign") }}
        </button>
      </div>
      <!-- right side -->
      <div class="flex items-center gap-2">
        <CustomActions v-if="customActions.length" :actions="customActions" />
      </div>
    </header>
    <div v-if="ticket.doc?.name" class="flex flex-1 overflow-x-hidden">
      <div class="flex flex-1 flex-col overflow-x-hidden">
        <div class="flex-1 flex flex-col">
          <Tabs
            :modelValue="tabIndex"
            :tabs="tabs"
            @update:modelValue="changeTabTo"
            class="[&_[role='tab']]:px-0 [&_[role='tablist']]:px-5 [&_[role='tablist']]:gap-7.5"
          >
            <template #tab-panel="{ tab }">
              <div v-if="tab.name === 'details'">
                <!-- ticket contact info -->
                <TicketAgentContact
                  v-if="contact.data"
                  :contact="contact.data"
                  :ticketId="ticket.doc?.name"
                  @email:open="communicationAreaRef.toggleEmailBox()"
                />
                <!-- feedback component -->
                <TicketFeedback
                  v-if="ticket.doc?.feedback_rating"
                  class="border-b px-6 py-3 text-base text-gray-600"
                  :ticket="ticket.doc"
                />
                <!-- SLA Section -->
                <h3 class="px-6 pt-3 font-semibold text-base">
                  {{ __("SLA") }}
                </h3>
                <TicketAgentDetails :ticket="ticket.doc" />
                <!-- Ticket Fields -->
                <h3 class="px-6 pt-3 font-semibold text-base">
                  {{ __("Details") }}
                </h3>
                <TicketAgentFields
                  :ticket="ticketWithFields"
                  @update="
                    ({ field, value }) =>
                      ticket.setValue.submit({ [field]: value })
                  "
                  class="!border-0"
                />
              </div>

              <!-- Rest Activities -->
              <TicketAgentActivities
                v-else
                ref="ticketAgentActivitiesRef"
                :activities="filterActivities(tab.name)"
                :title="tab.label"
                :ticket-status="ticket.doc?.status"
                @update="() => reloadTicket(props.ticketId)"
                @email:reply="
                  (e) => {
                    communicationAreaRef.replyToEmail(e);
                  }
                "
              />
            </template>
          </Tabs>
          <CommunicationArea
            class="sticky bottom-0 z-50 bg-white"
            ref="communicationAreaRef"
            v-model="ticket.doc"
            :ticketId="ticket.doc?.name"
            :to-emails="[ticket.doc.raised_by]"
            :cc-emails="[]"
            :bcc-emails="[]"
            :key="ticket.doc?.name"
            @update="
              () => {
                reloadTicket(props.ticketId);
                tabIndex !== 0 &&
                  ticketAgentActivitiesRef?.scrollToLatestActivity();
              }
            "
          />
        </div>
      </div>
    </div>
    <AssignmentModal
      v-if="ticket.doc?.name"
      v-model="showAssignmentModal"
      :assignees="parseAssignees"
      :docname="ticketId"
      :team="ticket.doc?.agent_group"
      doctype="HD Ticket"
      @update="() => reloadTicket(props.ticketId)"
    />
    <Dialog v-model="showSubjectDialog">
      <template #body-title>
        <h3>{{ __("Rename") }}</h3>
      </template>
      <template #body-content>
        <FormControl
          v-model="subjectInput"
          :type="'text'"
          size="sm"
          variant="subtle"
          :disabled="false"
          :label="__('New Subject')"
        />
      </template>
      <template #actions>
        <Button
          variant="solid"
          :disabled="!subjectInput"
          :loading="ticket.setValue.loading"
          @click="
            () => {
              ticket.setValue.submit({ subject: subjectInput });
              showSubjectDialog = false;
            }
          "
        >
          {{ __("Confirm") }}
        </Button>
        <Button class="ml-2" @click="showSubjectDialog = false">
          {{ __("Close") }}
        </Button>
      </template>
    </Dialog>
    <SetContactPhoneModal
      v-model="showPhoneModal"
      :name="contact.data?.name"
      @onUpdate="() => reloadTicket(props.ticketId)"
    />
  </div>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import {
  Breadcrumbs,
  call,
  createResource,
  Dialog,
  Dropdown,
  FormControl,
  Tabs,
  toast,
} from "frappe-ui";
import {
  computed,
  ComputedRef,
  h,
  onMounted,
  onUnmounted,
  provide,
  ref,
  watchEffect,
} from "vue";

import {
  AssignmentModal,
  CommunicationArea,
  LayoutHeader,
  MultipleAvatar,
} from "@/components";
import {
  ActivityIcon,
  CommentIcon,
  DetailsIcon,
  EmailIcon,
  IndicatorIcon,
  PhoneIcon,
} from "@/components/icons";
import { TicketAgentActivities } from "@/components/ticket";

import SetContactPhoneModal from "@/components/ticket/SetContactPhoneModal.vue";
import TicketAgentDetails from "@/components/ticket/TicketAgentDetails.vue";
import TicketAgentFields from "@/components/ticket/TicketAgentFields.vue";
import {
  parseField,
  setupCustomizations,
} from "@/composables/formCustomisation";
import { useScreenSize } from "@/composables/screen";
import { useActiveTabManager } from "@/composables/useActiveTabManager";
import { reloadTicket, useTicket } from "@/composables/useTicket";
import { globalStore } from "@/stores/globalStore";
import { getMeta } from "@/stores/meta";
import { useTelephonyStore } from "@/stores/telephony";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { useUserStore } from "@/stores/user";
import {
  ActivitiesSymbol,
  AssigneeSymbol,
  Customizations,
  CustomizationSymbol,
  FeedbackActivity,
  RecentSimilarTicketsSymbol,
  Resource,
  TabObject,
  TicketContactSymbol,
  TicketSymbol,
  TicketTab,
} from "@/types";
import { HDTicketStatus } from "@/types/doctypes";
import { storeToRefs } from "pinia";
import { useRouter } from "vue-router";

const telephonyStore = useTelephonyStore();
const { isCallingEnabled } = storeToRefs(telephonyStore);

const ticketStatusStore = useTicketStatusStore();
const { getUser } = useUserStore();
const router = useRouter();
const { $dialog } = globalStore();

const ticketAgentActivitiesRef = ref(null);
const communicationAreaRef = ref(null);
const subjectInput = ref(null);
const showPhoneModal = ref(false);
const customActions = ref([]);

const props = defineProps({
  ticketId: {
    type: String,
    required: true,
  },
});

const ticketComposable = computed(() => useTicket(props.ticketId));
const ticket = computed(() => ticketComposable.value.ticket);
const assignees = computed(() => ticketComposable.value.assignees);
const parseAssignees = computed(() =>
  (assignees.value.data || []).map(({ name }) => {
    const user = getUser(name);
    return {
      name,
      label: user.full_name || name,
      image: user.user_image || "",
    };
  })
);
const contact = computed(() => ticketComposable.value.contact);
const activities = computed(() => ticketComposable.value.activities);

const customizations: Resource<Customizations> = createResource({
  url: "helpdesk.helpdesk.doctype.hd_ticket.api.get_ticket_customizations",
  cache: ["HD Ticket", "customizations"],
  auto: true,
});

// Build fields from getMeta + customizations (same as TicketDetailsTab)
const { getField, getFields } = getMeta("HD Ticket");

function updateField(name: string, value: string) {
  ticket.value.setValue.submit({ [name]: value });
}

const customizationCtx = computed(() => ({
  doc: ticket.value?.doc,
  call,
  router,
  toast,
  $dialog,
  updateField,
  createToast: toast.create,
}));

watchEffect(async () => {
  if (customizations.data) {
    await setupCustomizations(customizations.data, customizationCtx.value);
    customActions.value = [...(customizations.data?._customActions || [])];
  }
});

const ticketFields = computed(() => {
  if (!customizations.data || !ticket.value.doc) return [];
  const fieldsMeta = getFields();
  if (!fieldsMeta || fieldsMeta.length === 0) return [];

  const coreFieldNames = [
    "ticket_type",
    "agent_group",
    "priority",
    "customer",
    "subject",
    "status",
  ];
  let custom_fields = customizations.data?.custom_fields || [];
  custom_fields = custom_fields.filter(
    (f) => !coreFieldNames.includes(f.fieldname)
  );

  return custom_fields
    .map((f) => {
      let fieldMeta = getField(f.fieldname);
      if (!fieldMeta) return null;
      fieldMeta = parseField(fieldMeta, ticket.value.doc);
      return {
        label: fieldMeta?.label || f.fieldname,
        fieldname: f.fieldname,
        fieldtype: fieldMeta?.fieldtype,
        options: fieldMeta?.options || "",
        placeholder:
          f.placeholder || `Enter ${fieldMeta?.label || f.fieldname}`,
        readonly: Boolean(fieldMeta.read_only),
        disabled: Boolean(fieldMeta.read_only),
        url_method: f.url_method || "",
        required: f.required || fieldMeta?.reqd || false,
        visible:
          fieldMeta.display_via_depends_on &&
          !fieldMeta.hidden &&
          (!!ticket.value.doc[f.fieldname] || !fieldMeta.read_only),
      };
    })
    .filter(Boolean);
});

// Merged ticket doc with computed fields for TicketAgentFields
const ticketWithFields = computed(() => ({
  ...ticket.value.doc,
  fields: ticketFields.value,
}));

provide(TicketSymbol, ticket);
provide(
  AssigneeSymbol,
  computed(() => ticketComposable.value.assignees)
);
provide(
  TicketContactSymbol,
  computed(() => ticketComposable.value.contact)
);
provide(
  CustomizationSymbol,
  computed(() => customizations)
);
provide(
  RecentSimilarTicketsSymbol,
  computed(() => ticketComposable.value.recentSimilarTickets)
);
provide(
  ActivitiesSymbol,
  computed(() => ticketComposable.value.activities)
);
provide("communicationArea", communicationAreaRef);
provide("makeCall", () => {
  if (!contact.value.data?.mobile_no && !contact.value.data?.phone) {
    showPhoneModal.value = true;
    return;
  }
  telephonyStore.makeCall({
    number: contact.value.data?.phone || contact.value.data?.mobile_no,
    doctype: "HD Ticket",
    docname: props.ticketId,
  });
});
provide("ticketId", props.ticketId);
provide("refreshTicket", () => reloadTicket(props.ticketId));
provide("onCallEnded", () => reloadTicket(props.ticketId));

const { isMobileView } = useScreenSize();

const showAssignmentModal = ref(false);
const showSubjectDialog = ref(false);

const breadcrumbs = computed(() => {
  let items = [{ label: __("Tickets"), route: { name: "TicketsAgent" } }];
  items.push({
    label: ticket.value.doc?.subject,
    route: { name: "TicketAgent" },
  });
  return items;
});

const dropdownOptions = computed(() =>
  ticketStatusStore.statuses.data?.map((o: HDTicketStatus) => ({
    label: o.label_agent,
    value: o.label_agent,
    onClick: () => ticket.value.setValue.submit({ status: o.label_agent }),
    icon: () =>
      h(IndicatorIcon, {
        class: o.parsed_color,
      }),
  }))
);

const tabs: ComputedRef<TabObject[]> = computed(() => {
  const _tabs = [
    {
      name: "details",
      label: __("Details"),
      icon: DetailsIcon,
      condition: () => isMobileView.value,
    },
    {
      name: "activity",
      label: __("Activity"),
      icon: ActivityIcon,
    },
    {
      name: "email",
      label: __("Emails"),
      icon: EmailIcon,
    },
    {
      name: "comment",
      label: __("Comments"),
      icon: CommentIcon,
    },
  ];

  if (isCallingEnabled.value) {
    _tabs.push({
      name: "call",
      label: __("Calls"),
      icon: PhoneIcon,
    });
  }
  return _tabs;
});

const { tabIndex, changeTabTo } = useActiveTabManager(tabs);

const _activities = computed(() => {
  if (!activities.value?.data) {
    return [];
  }

  const emailProps = activities.value.data.communications.map(
    (email, idx: number) => {
      return {
        subject: email.subject,
        content: email.content,
        sender: { name: email.user.email, full_name: email.user.name },
        to: email.recipients,
        type: "email",
        key: email.creation,
        cc: email.cc,
        bcc: email.bcc,
        creation: email.communication_date || email.creation,
        attachments: email.attachments,
        name: email.name,
        deliveryStatus: email.delivery_status,
        isFirstEmail: idx === 0,
      };
    }
  );

  const commentProps = activities.value.data.comments.map((comment) => {
    return {
      name: comment.name,
      type: "comment",
      key: comment.creation,
      commentedBy: comment.commented_by,
      commenter: comment.user.name,
      creation: comment.creation,
      content: comment.content,
      attachments: comment.attachments,
    };
  });

  activities.value.data.history.map((h) => {
    if (h.action && h.owner && h.action.includes(h.owner)) {
      h.action = h.action.replace(h.owner, "themselves");
    }
    return h;
  });

  const historyProps = [
    ...activities.value.data.history,
    ...activities.value.data.views,
  ].map((h) => {
    return {
      type: "history",
      key: h.creation,
      content: h.action ? h.action : __("viewed this"),
      creation: h.creation,
      user: h.user.name + " ",
    };
  });

  const callProps = activities.value.data.calls.map((call) => {
    return {
      ...call,
      type: "call",
      name: call.name,
      key: call.creation,
      call_type: call.type,
      content: `${call.caller || "Unknown"} made a call to ${
        call.receiver || "Unknown"
      }`,
      duration: call.duration ? call.duration + "s" : "0s",
    };
  });

  const sorted = [
    ...emailProps,
    ...commentProps,
    ...historyProps,
    ...callProps,
  ].sort(
    (a, b) => new Date(a.creation).getTime() - new Date(b.creation).getTime()
  );

  const data = [];
  let i = 0;

  while (i < sorted.length) {
    const currentActivity = sorted[i];
    if (currentActivity.type === "history") {
      currentActivity.relatedActivities = [currentActivity];
      for (let j = i + 1; j < sorted.length + 1; j++) {
        const nextActivity = sorted[j];

        if (
          nextActivity &&
          nextActivity.user === currentActivity.user &&
          nextActivity.content !== "viewed this" &&
          !nextActivity.content.includes("assigned") &&
          !nextActivity.content.includes("unassigned")
        ) {
          currentActivity.relatedActivities.push(nextActivity);
        } else {
          data.push(currentActivity);
          i = j - 1;
          break;
        }
      }
    } else {
      data.push(currentActivity);
    }
    i++;
  }

  if (ticket.value.doc?.feedback_rating === 0) {
    return data;
  }
  const feedbackActivity: FeedbackActivity[] = [
    {
      type: "feedback",
      key: "feedback-activity",
      feedback_rating: ticket.value?.doc?.feedback_rating,
      feedback_extra: ticket.value?.doc?.feedback_extra,
      feedback: ticket.value?.doc?.feedback,
      sender: {
        name: ticket.value?.doc?.raised_by,
        full_name: ticket.value?.doc?.contact,
      },
    },
  ];
  data.push(...feedbackActivity);

  return data;
});

function filterActivities(eventType: TicketTab) {
  if (eventType === "activity") {
    return _activities.value;
  }
  return _activities.value.filter((activity) => activity.type === eventType);
}

onMounted(() => {
  document.title = props.ticketId;
});

onUnmounted(() => {
  document.title = "Helpdesk";
});
</script>
<style scoped>
:deep(.breadcrumb-item span),
:deep(a span) {
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  white-space: normal !important;
}
</style>
