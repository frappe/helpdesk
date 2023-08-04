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
      <div v-for="t in tickets" :key="t.name">
        <RouterLink :to="t.to" target="_blank" class="flex items-start gap-2">
          <IconWebLink class="h-4 w-4 text-gray-600" />
          <div class="text-base text-gray-800">{{ t.subject }}</div>
        </RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { isEmpty } from "lodash";
import { computed, ref } from "vue";
import { createListResource } from "frappe-ui";
import { AGENT_PORTAL_TICKET } from "@/router";
import IconCaretDown from "~icons/lucide/chevron-down";
import IconCaretUp from "~icons/lucide/chevron-up";
import IconWebLink from "~icons/lucide/external-link";
import { useTicket } from "./data";

class Ticket {
  constructor(public name: number, public subject: string) {}

  get to() {
    return {
      name: AGENT_PORTAL_TICKET,
      params: {
        ticketId: this.name,
      },
    };
  }
}

const ticket = useTicket();
const data = computed(() => ticket.value.data);
const isExpanded = ref(true);

const ticketRes = createListResource({
  doctype: "HD Ticket",
  fields: ["name", "subject"],
  filters: {
    name: ["!=", data.value.name],
    contact: data.value.contact.name,
    status: "Open",
  },
  orderBy: "modified desc",
  auto: true,
});

const tickets = computed(
  () => ticketRes.data?.map((t: Ticket) => new Ticket(t.name, t.subject)) || []
);
</script>
