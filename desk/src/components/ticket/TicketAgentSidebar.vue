<template>
  <div class="flex w-[382px] flex-col justify-between border-l">
    <div class="h-10.5 flex items-center justify-between border-b px-5 py-2.5">
      <span class="text-lg font-semibold">About this Ticket</span>
      <span>#{{ ticket.name }}</span>
    </div>
    <TicketAgentCustomer
      v-if="ticket.customer"
      @email:open="(e) => emit('email:open', e)"
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
    <TicketAgentFields :ticket="ticket" @update="update" />
    <div v-if="ticket.feedback_rating" class="px-6 py-3 text-gray-600">
      <div class="flex">
        <div class="w-[106px] pb-1.5 text-sm">Feedback</div>
        <div class="px-1.5">
          <StarRating :rating="ticket.feedback_rating" />
        </div>
      </div>
      <div class="pb-1.5 text-base">
        {{ ticket.feedback_text }}
      </div>
      <div class="pb-1.5 text-sm">
        {{ ticket.feedback_extra }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineEmits } from "vue";
import { StarRating } from "@/components";
import TicketAgentDetails from "./TicketAgentDetails.vue";
import TicketAgentCustomer from "./TicketAgentCustomer.vue";
import TicketAgentFields from "./TicketAgentFields.vue";

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
