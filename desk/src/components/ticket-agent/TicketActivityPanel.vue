<template>
  <Tabs v-model="tabIndex" :tabs="tabs">
    <TabList />
    <TabPanel v-slot="{ tab }" class="flex-1">
      <TicketAgentActivities
        v-if="Boolean(activities.data)"
        ref="ticketAgentActivitiesRef"
        :activities="filterActivities(tab.name as TicketTab)"
        :title="tab.label"
        :ticket-status="ticket.doc.status"
        @email:reply="
          (e) => {
            communicationAreaRef.replyToEmail(e);
          }
        "
      />
      <div v-else class="flex items-center justify-center flex-col mt-20">
        <LoadingIndicator :scale="8" class="text-ink-gray-5" />
        <p class="text-xl font-medium text-ink-gray-5 absolute top-[50%]">
          Loading...
        </p>
      </div>
    </TabPanel>
  </Tabs>
  <!-- Comm Area -->
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
        ticketAgentActivitiesRef.scrollToLatestActivity();
      }
    "
  />
</template>

<script setup lang="ts">
import { CommunicationArea } from "@/components";
import { ActivityIcon, CommentIcon, EmailIcon } from "@/components/icons";
import { ActivitiesSymbol, TabObject, TicketSymbol, TicketTab } from "@/types";
import { LoadingIndicator, TabList, TabPanel, Tabs } from "frappe-ui";
import { computed, inject, ref } from "vue";
import TicketAgentActivities from "../ticket/TicketAgentActivities.vue";
const ticket = inject(TicketSymbol);
const activities = inject(ActivitiesSymbol);

const tabIndex = ref(0);
const ticketAgentActivitiesRef = ref(null);
const communicationAreaRef = ref(null);

const tabs: TabObject[] = [
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

// TODO: refactor for pagination
// can be done once we sort out the backend
const _activities = computed(() => {
  if (
    activities.value?.loading ||
    ticket.value?.loading ||
    !activities.value?.data
  ) {
    return [];
  }

  const emailProps = activities.value?.data?.communications.map(
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
  // console.log(historyProps);

  const sorted = [...emailProps, ...commentProps, ...historyProps].sort(
    (a, b) => new Date(a.creation) - new Date(b.creation)
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

  return data;
});

function filterActivities(eventType: TicketTab) {
  if (eventType === "activity") {
    return _activities.value;
  }
  return _activities.value.filter((activity) => activity.type === eventType);
}
</script>

<style scoped></style>
