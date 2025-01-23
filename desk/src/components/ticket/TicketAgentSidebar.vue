<template>
  <div class="flex w-[382px] flex-col justify-between border-l">
    <div class="h-[2.83rem] flex items-center justify-between border-b px-5">
      <span
        class="cursor-copy text-lg font-semibold"
        @click="copyToClipboard(ticket.name, ticket.name)"
        >#{{ ticket.name }}</span
      >
    </div>
    <TicketAgentContact
      :contact="ticket.contact"
      @email:open="(e) => emit('email:open', e)"
    />
    <!-- feedback component -->
    <TicketFeedback
      v-if="ticket.feedback_rating"
      class="border-b px-6 py-3 text-base text-gray-600"
      :ticket="ticket"
    />
    <!-- ticket details -->
    <TicketAgentDetails
      :agreement-status="ticket.agreement_status"
      :first-responded-on="ticket.first_responded_on"
      :response-by="ticket.response_by"
      :resolution-date="ticket.resolution_date"
      :resolution-by="ticket.resolution_by"
      :ticket-created-on="ticket.creation"
      :source="ticket.via_customer_portal ? 'Portal' : 'Mail'"
    />
    <!-- fields -->
    <TicketAgentFields :ticket="ticket" @update="update" />
  </div>
</template>

<script setup lang="ts">
import TicketAgentDetails from "./TicketAgentDetails.vue";
import TicketAgentContact from "./TicketAgentContact.vue";
import TicketAgentFields from "./TicketAgentFields.vue";
import { copyToClipboard } from "@/utils";

const props = defineProps({
  ticket: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(["update", "email:open"]);

function update(val) {
  emit("update", val);
}
</script>
