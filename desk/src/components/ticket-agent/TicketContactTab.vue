<template>
  <!-- TODO: handle ellipsis -->
  <div>
    <div class="flex gap-3 items-center px-5 py-2.5">
      <Avatar :label="user.name" :image="user.user_image" size="2xl" />
      <p class="text-ink-gray-8 font-medium text-xl">
        {{ user.name }}
      </p>
    </div>
    <div class="border-b px-5 text-ink-gray-5 pb-2">
      <!-- Email Id -->
      <div class="flex gap-2 items-center p-1.5">
        <EmailIcon class="size-4" />
        <p class="text-p-sm text-ink-gray-6 hover:underline cursor-pointer">
          {{ user.email }}
        </p>
        <CopyIcon class="size-4 cursor-pointer" />
      </div>
      <!-- Mobile Number -->
      <div class="flex gap-2 items-center p-1.5">
        <LucidePhone class="size-4" />
        <p class="text-p-sm text-ink-gray-6 hover:underline cursor-pointer">
          9997772221
        </p>
        <CopyIcon class="size-4 cursor-pointer" />
      </div>
    </div>
    <!-- Recent Tickets -->
    <div class="px-5">
      <Section
        :label="section.label"
        :hideLabel="section.hideLabel"
        :opened="section.opened"
      >
        <template #header="{ opened, hide, toggle }">
          <div class="flex gap-2.5 items-center py-[13px] justify-between">
            <span
              class="text-ink-gray-8 font-medium text-base cursor-pointer select-none"
              @click="toggle"
            >
              Recent Tickets
            </span>
            <LucideChevronDown
              class="size-4 text-ink-gray-6 cursor-pointer"
              :class="{ 'rotate-180': opened }"
              @click="toggle"
            />
          </div>
        </template>
        <ul>
          <li
            v-for="ticket in section.tickets"
            :key="ticket.name"
            class="py-2.5 border-b last:border-0"
          >
            <p class="text-base text-ink-gray-8">{{ ticket.subject }}</p>
            <div class="flex items-center justify-between">
              <p class="text-base text-ink-gray-5">
                {{ ticket.created + " &#183; " + "#" + ticket.name }}
              </p>
              <p
                class="px-1.5 py-[3px] text-sm rounded-sm max-w-[80px] text-center truncate h-5"
                :class="getStatusColor(ticket.status)"
              >
                {{ ticket.status }}
              </p>
            </div>
          </li>
        </ul>
      </Section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { useUserStore } from "@/stores/user";
import { TicketSymbol } from "@/types";
import { Avatar } from "frappe-ui";
import { inject } from "vue";
import { CopyIcon } from "../icons";
import EmailIcon from "../icons/EmailIcon.vue";
import Section from "../Section.vue";

const ticket = inject(TicketSymbol);

const { getUser } = useUserStore();
const user = getUser(ticket.value.doc.contact);
const { getStatus, colorMap } = useTicketStatusStore();

function getStatusColor(status: string) {
  let { color } = getStatus(status);

  if (colorMap[color]) {
    return colorMap[color];
  } else {
    return colorMap["Default"];
  }
}

const recentTickets = [
  {
    name: "TCK-0001",
    subject: "Unable to login to my account",
    status: "Replied",
    created: "Jun 02, 20225",
  },
  {
    name: "TCK-0002",
    subject: "Payment not reflecting",
    status: "On Hold",
    created: "Jun 05, 2024",
  },
  {
    name: "TCK-0003",
    subject: "Feature request for dark mode",
    status: "Open",
    created: "Jun 10, 2024",
  },
];

const section = {
  label: "Recent Tickets",
  hideLabel: false,
  opened: true,
  tickets: recentTickets,
};
</script>

<style scoped></style>
