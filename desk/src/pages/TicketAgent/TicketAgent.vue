<template>
  <div v-if="!ticket.get?.loading" class="flex-1">
    <TicketHeader />
    <div class="h-full flex overflow-hidden">
      <div class="flex-1 flex flex-col">
        <!-- Tabs -->
        <TicketActivityPanel />
        <!-- Comm Area -->
        <!-- <CommunicationArea ref="communicationAreaRef" /> -->
      </div>

      <!-- Sidebar with Resizer -->
      <TicketSidebar />
    </div>
  </div>
</template>

<script setup lang="ts">
import TicketActivityPanel from "@/components/ticket-agent/TicketActivityPanel.vue";
import TicketHeader from "@/components/ticket-agent/TicketHeader.vue";
import TicketSidebar from "@/components/ticket-agent/TicketSidebar.vue";
import { useTicket } from "@/composables/useTicket";
import {
  AssigneeSymbol,
  Customizations,
  CustomizationSymbol,
  RecentSimilarTicketsSymbol,
  Resource,
  TicketContactSymbol,
  TicketSymbol,
} from "@/types";
import { createResource } from "frappe-ui";
import { computed, provide } from "vue";

const props = defineProps({
  ticketId: {
    type: String,
    required: true,
  },
});

const ticketComposable = computed(() => useTicket(props.ticketId));
const ticket = computed(() => ticketComposable.value.ticket);
const customizations: Resource<Customizations> = createResource({
  url: "helpdesk.helpdesk.doctype.hd_ticket.api.get_ticket_customizations",
  cache: ["HD Ticket", "customizations"],
  auto: true,
});

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
</script>

<style>
.breadcrumbs button {
  background-color: inherit !important;
  &:hover,
  &:focus {
    background-color: inherit !important;
  }
}
</style>
