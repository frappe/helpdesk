<template>
  <Tabs
    :modelValue="tabIndex"
    :tabs="tabs"
    @update:modelValue="changeTabTo"
    class="[&_[role='tab']]:px-0 [&_[role='tablist']]:px-5 [&_[role='tablist']]:gap-7.5 [&_[role='tablist']]:flex-shrink-0 [&_[role='tabpanel'][data-state='active']]:flex-1"
  >
    <template #tab-panel="{ tab }">
      <TicketAgentActivities
        v-if="Boolean(activities.data)"
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

      <div v-else class="flex items-center justify-center flex-col flex-1">
        <Button :loading="true" variant="ghost" size="2xl" />
        <p class="text-xl font-medium text-ink-gray-5">Loading...</p>
      </div>
    </template>
  </Tabs>

  <!-- Communication Area -->
  <CommunicationArea
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

import {
  ActivityIcon,
  CommentIcon,
  EmailIcon,
  PhoneIcon,
} from "@/components/icons";

import LucideListTodo from "~icons/lucide/list-todo";

import { __ } from "@/translation";

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

const ticket = inject(TicketSymbol);
const activities = inject(ActivitiesSymbol);

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
    {
      name: "task",
      label: __("Tasks"),
      icon: LucideListTodo,
    },
  ];

  if (isCallingEnabled.value) {
    _tabs.push({
      name: "call",
      label: "Calls",
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

  // EMAILS
  const emailProps =
    activities.value?.data?.communications?.map((email: any, idx: number) => {
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
    }) || [];

  // COMMENTS
  const commentProps =
    activities.value?.data?.comments?.map((comment: any) => {
      return {
        name: comment.name,
        type: "comment",
        key: comment.creation,
        commentedBy: comment.commented_by,
        commenter: comment.user?.name,
        creation: comment.creation,
        content: comment.content,
        attachments: comment.attachments,
      };
    }) || [];

  // HISTORY — mutate in place to replace owner name with "themselves"
  activities.value?.data?.history?.forEach((h: any) => {
    if (h.action && h.owner && h.action.includes(h.owner)) {
      h.action = h.action.replace(h.owner, "themselves");
    }
  });

  const historyProps = [
    ...(activities.value?.data?.history || []),
    ...(activities.value?.data?.views || []),
  ].map((h: any) => {
    return {
      type: "history",
      key: h.creation,
      content: h.action ? h.action : "viewed this",
      creation: h.creation,
      user: h.user?.name + " ",
    };
  });

  // CALLS
  const callProps =
    activities.value?.data?.calls?.map((call: any) => {
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
    }) || [];

  // TASKS — read from activities.data.tasks (returned by get_ticket_activities)
  const taskProps =
    activities.value?.data?.tasks?.map((task: any) => {
      return {
        ...task,
        type: "task",
        key: task.name, // use name (unique ID) as key, not creation
        creation: task.creation,
      };
    }) || [];

  // MERGE + SORT all activity types by creation time
  const sorted = [
    ...emailProps,
    ...commentProps,
    ...historyProps,
    ...callProps,
    ...taskProps,
  ].sort(
    (a: any, b: any) =>
      new Date(a.creation).getTime() - new Date(b.creation).getTime()
  );

  const data: any[] = [];
  let i = 0;

  while (i < sorted.length) {
    const currentActivity: any = sorted[i];

    if (currentActivity.type === "history") {
      currentActivity.relatedActivities = [currentActivity];

      for (let j = i + 1; j < sorted.length + 1; j++) {
        const nextActivity: any = sorted[j];

        if (
          nextActivity &&
          nextActivity.user === currentActivity.user &&
          nextActivity.content !== "viewed this" &&
          !nextActivity.content?.includes("assigned") &&
          !nextActivity.content?.includes("unassigned")
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

  // FEEDBACK — always last
  if ((ticket.value?.doc?.feedback_rating || 0) !== 0) {
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
  }

  return data;
});

function filterActivities(eventType: TicketTab) {
  if (eventType === "activity") {
    return _activities.value;
  }

  return _activities.value.filter(
    (activity: any) => activity.type === eventType
  );
}
</script>
