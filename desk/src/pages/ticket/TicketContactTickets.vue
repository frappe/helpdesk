<template>
  <div
    v-if="!isEmpty(tickets)"
    class="py-4 text-base"
    :class="{
      'border-b': !isExpanded,
    }"
  >
    <div
      class="flex cursor-pointer items-center justify-between"
      @click="isExpanded = !isExpanded"
    >
      <div class="font-medium text-gray-800">Open tickets</div>
      <LucideChevronUp v-if="isExpanded" class="w-4 text-gray-700" />
      <LucideChevronDown v-else class="w-4 text-gray-700" />
    </div>
    <ul v-if="isExpanded" class="list-inside list-disc space-y-2 py-4">
      <li v-for="t in tickets.data" :key="t.name">
        <RouterLink
          :to="{
            name: 'TicketAgent',
            params: {
              ticketId: t.name,
            },
          }"
          target="_blank"
          class="leading-normal"
        >
          {{ t.subject }}
        </RouterLink>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { inject, ref } from "vue";
import { createListResource } from "frappe-ui";
import { isEmpty } from "lodash";
import { ITicket } from "./symbols";

const ticket = inject(ITicket);
const isExpanded = ref(true);
const tickets = createListResource({
  doctype: "HD Ticket",
  auto: true,
  fields: ["name", "subject"],
  filters: {
    name: ["!=", ticket.data.name],
    contact: ticket.data.contact.name,
    status: "Open",
  },
  orderBy: "modified desc",
});
</script>
