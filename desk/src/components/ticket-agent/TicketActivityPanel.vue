<template>
  <Tabs v-model="tabIndex" :tabs="tabs">
    <TabList />
    <TabPanel v-slot="{ tab }" class="flex-1">
      <TicketAgentActivities
        :activities="activities"
        :title="tab.label"
        :ticket-status="ticket.doc.status"
      />
    </TabPanel>
  </Tabs>
</template>

<script setup lang="ts">
import { ActivityIcon, CommentIcon, EmailIcon } from "@/components/icons";
import { TabObject, TicketSymbol } from "@/types";
import { TabList, TabPanel, Tabs } from "frappe-ui";
import { inject, ref } from "vue";
import TicketAgentActivities from "../ticket/TicketAgentActivities.vue";

const ticket = inject(TicketSymbol);

const tabIndex = ref(0);
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
const activities = [
  {
    subject: "Re: Ticket for customer Timeless",
    content: "<h3>Issue:</h3><p>Issue with billing</p>",
    sender: {
      name: "admin@example.com",
      full_name: "admin@example.com",
    },
    to: null,
    type: "email",
    key: "2025-08-20 15:21:32.578369",
    cc: null,
    bcc: null,
    creation: "2025-08-20 15:21:32.574604",
    attachments: [],
    name: "2jdbm4fh5d",
    deliveryStatus: "",
    isFirstEmail: true,
  },
  {
    subject: "Re: Ticket for customer Timeless",
    content: "<p>lkpjl\\</p>",
    sender: {
      name: "admin@example.com",
      full_name: "admin@example.com",
    },
    to: "admin@example.com",
    type: "email",
    key: "2025-08-22 12:59:31.645557",
    cc: "",
    bcc: "",
    creation: "2025-08-22 12:59:31.642100",
    attachments: [],
    name: "6sklpejf9k",
    deliveryStatus: "",
    isFirstEmail: false,
  },
];
</script>

<style scoped></style>
