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
        :ticket-id="String(ticket.doc?.name || '')"
        @email:reply="(e) => communicationAreaRef?.replyToEmail(e)"
        @update="
          () => {
            activities.reload();
            ticketAgentActivitiesRef?.scrollToLatestActivity();
          }
        "
      />
      <!-- <div v-else class="flex items-center justify-center flex-col flex-1">
        <Button :loading="true" variant="ghost" size="2xl" />
    </template>
  </Tabs>

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
import { TaskIcon } from "@/components/icons";
import { __ } from "@/translation";

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
    { name: "activity", label: __("Activity"), icon: ActivityIcon },
    { name: "email", label: __("Emails"), icon: EmailIcon },
    { name: "comment", label: __("Comments"), icon: CommentIcon },
    { name: "task", label: __("Tasks"), icon: TaskIcon },
  ];
  if (isCallingEnabled.value) {
    _tabs.push({ name: "call", label: __("Calls"), icon: PhoneIcon });
  }
  return _tabs;
});

const { tabIndex, changeTabTo } = useActiveTabManager(tabs);

const _activities = computed(() => {
  if (!activities.value?.data) return [];

  const emailProps = (activities.value.data.communications || []).map(
    (email: any, idx: number) => ({
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
    })
  );

  const commentProps = (activities.value.data.comments || []).map(
    (comment: any) => ({
      name: comment.name,
      type: "comment",
      key: comment.creation,
      commentedBy: comment.commented_by,
      commenter: comment.user?.name,
      creation: comment.creation,
      content: comment.content,
      attachments: comment.attachments,
    })
  );

  (activities.value.data.history || []).forEach((h: any) => {
    if (h.action && h.owner && h.action.includes(h.owner)) {
      h.action = h.action.replace(h.owner, "themselves");
    }
  });

  const historyProps = [
    ...(activities.value.data.history || []),
    ...(activities.value.data.views || []),
  ].map((h: any) => ({
    type: "history",
    key: h.creation,
    content: h.action ? h.action : __("viewed this"),
    creation: h.creation,
    user: (h.user?.name || "") + " ",
  }));

  const callProps = (activities.value.data.calls || []).map((call: any) => ({
    ...call,
    type: "call",
    key: call.creation,
    call_type: call.type,
    content: `${call.caller || "Unknown"} made a call to ${
      call.receiver || "Unknown"
    }`,
    duration: call.duration ? call.duration + "s" : "0s",
  }));

  const taskProps = (activities.value.data.tasks || []).map((task: any) => ({
    type: "task",
    key: task.name,
    name: task.name,
    title: task.title,
    description: task.description,
    status: task.status,
    priority: task.priority,
    due_date: task.due_date,
    assigned_to: task.assigned_to,
    reference_doctype: task.reference_doctype || "HD Ticket",
    reference_docname:
      task.reference_docname || String(ticket.value?.doc?.name || ""),
    creation: task.creation,
    owner: task.owner,
  }));

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
    const cur: any = sorted[i];
    if (cur.type === "history") {
      cur.relatedActivities = [cur];
      for (let j = i + 1; j < sorted.length + 1; j++) {
        const next: any = sorted[j];
        if (
          next &&
          next.user === cur.user &&
          next.content !== __("viewed this") &&
          !next.content?.includes("assigned") &&
          !next.content?.includes("unassigned")
        ) {
          cur.relatedActivities.push(next);
        } else {
          data.push(cur);
          i = j - 1;
          break;
        }
      }
    } else {
      data.push(cur);
    }
    i++;
  }

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
  if (eventType === "activity") return _activities.value;
  return _activities.value.filter((a: any) => a.type === eventType);
}
</script>
