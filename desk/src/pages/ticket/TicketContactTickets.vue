<template>
  <div
    v-if="!isEmpty(tickets)"
    class="select-none py-4"
    :class="{
      'border-b': !isExpanded,
    }"
  >
    <div
      class="flex cursor-pointer items-center justify-between"
      @click="isExpanded = !isExpanded"
    >
      <div class="text-base font-medium text-gray-800">Open tickets</div>
      <IconCaretUp v-if="isExpanded" class="h-4 w-4 text-gray-600" />
      <IconCaretDown v-else class="h-4 w-4 text-gray-600" />
    </div>
    <div v-if="isExpanded" class="flex flex-col gap-4 py-4">
      <div v-for="t in tickets.data" :key="t.name">
        <RouterLink
          :to="{
            name: 'TicketAgent',
            params: {
              ticketId: t.name,
            },
          }"
          target="_blank"
          class="flex items-start gap-2"
        >
          <IconWebLink class="h-4 w-4 text-gray-600" />
          <div class="text-base text-gray-800">{{ t.subject }}</div>
        </RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { inject, ref } from "vue";
import { createListResource } from "frappe-ui";
import { isEmpty } from "lodash";
import IconCaretDown from "~icons/lucide/chevron-down";
import IconCaretUp from "~icons/lucide/chevron-up";
import IconWebLink from "~icons/lucide/external-link";
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
