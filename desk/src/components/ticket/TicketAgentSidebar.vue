<template>
  <div class="flex w-[352px] flex-col justify-between border-l">
    <div class="h-10.5 flex items-center justify-between border-b px-5 py-2.5">
      <span class="text-lg font-semibold">About This Ticket</span>
      <span>#{{ ticket.name }}</span>
    </div>
    <TicketAgentCustomer
      :name="ticket.customer"
      email="abc@email.com"
      website="www.example.com"
    />
    <TicketAgentDetails
      :first-responded-on="ticket.first_responded_on"
      :response-by="ticket.response_by"
      :resolution-date="ticket.resolution_date"
      :resolution-by="ticket.resolution_by"
      :source="ticket.via_customer_portal ? 'Portal' : 'Mail'"
    />
    <TicketAgentFields :ticket="ticket" />
  </div>
</template>

<script setup lang="ts">
import TicketAgentDetails from "./TicketAgentDetails.vue";
import TicketAgentCustomer from "./TicketAgentCustomer.vue";
import TicketAgentFields from "./TicketAgentFields.vue";

const props = defineProps({
  ticket: {
    type: Object,
    required: true,
  },
});
</script>
