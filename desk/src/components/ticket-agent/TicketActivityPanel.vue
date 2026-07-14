<template>
  <Tabs
    :modelValue="tabIndex"
    :tabs="tabs"
    @update:modelValue="changeTabTo"
    class="[&_[role='tab']]:px-0 [&_[role='tablist']]:px-5 [&_[role='tablist']]:gap-7.5 [&_[role='tablist']]:flex-shrink-0 [&_[role='tabpanel'][data-state='active']]:flex-1"
  >
    <template #tab-panel="{ tab }">
      <!-- WhatsApp is its own medium: a self-contained chat (thread + composer),
           not part of the email/comment timeline. -->
      <WhatsAppConversation
        v-if="tab.name === 'whatsapp'"
        :messages="whatsappActivities"
        :ticket-id="String(ticket.doc?.name)"
        @update="() => activities.reload()"
      />
      <TicketAgentActivities
        v-else-if="Boolean(activities.data)"
        ref="ticketAgentActivitiesRef"
        :activities="filterActivities(tab.name as TicketTab)"
        :title="tab.label"
        :ticket-status="ticket.doc.status"
        @email:reply="
          (e) => {
            communicationAreaRef?.replyToEmail(e);
          }
        "
        @update="
          () => {
            activities.reload();
            ticketAgentActivitiesRef?.scrollToLatestActivity();
          }
        "
      />
    </template>
  </Tabs>
  <!-- Email/comment composer — hidden on WhatsApp, which composes inline. -->
  <CommunicationArea
    v-if="activeTabName !== 'whatsapp'"
    ref="communicationAreaRef"
    :ticketId="String(ticket.doc?.name)"
    :to-emails="[ticket.doc?.raised_by]"
    :cc-emails="[]"
    :bcc-emails="[]"
    :key="ticket.doc?.name"
    @update="
      () => {
        activities.reload();
        ticketAgentActivitiesRef?.scrollToLatestActivity();
      }
    "
  />
</template>

<script setup lang="ts">
import CommunicationArea from "@/components/CommunicationArea.vue";
import WhatsAppConversation from "@/components/whatsapp/WhatsAppConversation.vue";
import {
  ActivityIcon,
  CommentIcon,
  EmailIcon,
  PhoneIcon,
  WhatsAppIcon,
} from "@/components/icons";
import { whatsAppEnabled } from "@/composables/whatsapp";
import { useActiveTabManager } from "@/composables/useActiveTabManager";
import { useTelephonyStore } from "@/stores/telephony";
import {
  ActivitiesSymbol,
  FeedbackActivity,
  TabObject,
  TicketSymbol,
  TicketTab,
} from "@/types";
import { Button, Tabs } from "frappe-ui";
import { storeToRefs } from "pinia";
import { computed, ComputedRef, inject, ref } from "vue";
import { TicketAgentActivities } from "../ticket";

const ticket = inject(TicketSymbol)!;
const activities = inject(ActivitiesSymbol)!;

const ticketAgentActivitiesRef = ref<InstanceType<
  typeof TicketAgentActivities
> | null>(null);
const communicationAreaRef = ref<InstanceType<typeof CommunicationArea> | null>(
  null
);
const telephonyStore = useTelephonyStore();
const { isCallingEnabled } = storeToRefs(telephonyStore);

const tabs: ComputedRef<TabObject[]> = computed(() => {
  const _tabs: TabObject[] = [
    {
      name: "activity",
      label: "Activity",
      icon: ActivityIcon,
    },
    {
      name: "email",
      label: "Emails",
      icon: EmailIcon,
    },
    {
      name: "comment",
      label: "Comments",
      icon: CommentIcon,
    },
  ];

  if (isCallingEnabled.value) {
    _tabs.push({
      name: "call",
      label: "Calls",
      icon: PhoneIcon,
    });
  }

  // Only surface WhatsApp once the frappe_whatsapp transport app is configured.
  if (whatsAppEnabled.value) {
    _tabs.push({
      name: "whatsapp",
      label: "WhatsApp",
      icon: WhatsAppIcon,
    });
  }
  return _tabs;
});

const { tabIndex, changeTabTo } = useActiveTabManager(tabs);

const activeTabName = computed(() => tabs.value[tabIndex.value]?.name);

// TODO: refactor for pagination
// can be done once we sort out the backend
// sender mail will be  user using portal
const _activities = computed(() => {
  if (!activities.value?.data) {
    return [];
  }
  const emailProps = activities.value?.data?.communications.map(
    (email, idx: number) => {
      return {
        subject: email.subject,
        content: email.content,
        sender: {
          name: email.user.email,
          full_name: email.user.name,
        },
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
    // }
    h.action;
    h.owner;
    // if h.actions includes h.owner, replace it with 'themselves'
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
      content: h.action ? h.action : "viewed this",
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
  ].sort((a, b) => new Date(a.creation) - new Date(b.creation));
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
  // add feedback data at the last always
  // name is email
  // full_name is name

  if (ticket.value.doc.feedback_rating === 0) {
    return data;
  }
  let feedbackActivity: FeedbackActivity[] = [
    {
      type: "feedback",
      key: "feedback-activity",
      feedback_rating: ticket.value?.doc.feedback_rating,
      feedback_extra: ticket.value?.doc.feedback_extra,
      feedback: ticket.value?.doc.feedback,
      sender: {
        name: ticket.value?.doc.raised_by,
        full_name: ticket.value?.doc.contact,
      },
    },
  ];
  data.push(...feedbackActivity);

  return data;
});

// The WhatsApp thread is the contact's whole conversation (omnichannel), kept
// out of the general Activity feed so it does not drown emails and comments.
// Each message keeps its Incoming/Outgoing under `direction`, freeing `type` to
// be the activity discriminator the timeline switches on.
const whatsappActivities = computed(() => {
  const messages = activities.value?.data?.whatsapp;
  if (!messages) return [];
  return messages.map((m) => ({
    ...m,
    type: "whatsapp",
    direction: m.type,
    key: m.name,
    content: m.message || "",
    creation: m.creation,
  }));
});

function filterActivities(eventType: TicketTab) {
  // whatsapp is not handled here: its tab renders WhatsAppConversation directly
  // (fed by whatsappActivities), never TicketAgentActivities.
  if (eventType === "activity") {
    return _activities.value;
  }
  return _activities.value.filter((activity) => activity.type === eventType);
}
</script>
