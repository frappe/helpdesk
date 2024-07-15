<template>
  <div class="flex w-[382px] flex-col justify-between border-l">
    <div class="h-10.5 flex items-center justify-between border-b px-5 py-2.5">
      <span class="cursor-copy text-lg font-semibold" @click="copyToClipboard()"
        >#{{ ticket.name }}</span
      >
    </div>
    <TicketAgentContact
      :contact="ticket.contact"
      @email:open="(e) => emit('email:open', e)"
    />
    <div
      v-if="ticket.feedback_rating"
      class="border-b px-6 py-3 text-base text-gray-600"
    >
      <div class="flex">
        <div class="min-w-[106px] pb-1.5">Rating</div>
        <div class="px-1.5">
          <StarRating :rating="ticket.feedback_rating" />
        </div>
      </div>
      <div class="flex">
        <div class="w-[106px] pb-1.5">Feedback</div>
        <div class="px-1.5 text-gray-800">
          {{ ticket.feedback_text }}
        </div>
      </div>
      <div v-if="ticket.feedback_extra" class="flex">
        <div class="min-w-[106px] pb-1.5">Comment</div>
        <div class="px-1.5 text-gray-800">
          {{ ticket.feedback_extra }}
        </div>
      </div>
    </div>
    <TicketAgentDetails
      :agreement-status="ticket.agreement_status"
      :first-responded-on="ticket.first_responded_on"
      :response-by="ticket.response_by"
      :resolution-date="ticket.resolution_date"
      :resolution-by="ticket.resolution_by"
      :ticket-created-on="ticket.creation"
      :source="ticket.via_customer_portal ? 'Portal' : 'Mail'"
    />
    <TicketAgentFields :ticket="ticket" @update="update" />
  </div>
</template>

<script setup lang="ts">
import { StarRating } from "@/components";
import TicketAgentDetails from "./TicketAgentDetails.vue";
import TicketAgentContact from "./TicketAgentContact.vue";
import TicketAgentFields from "./TicketAgentFields.vue";
import { createToast } from "@/utils";

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

function copyToClipboard() {
  navigator.clipboard.writeText(`${props.ticket.name}`);
  createToast({
    title: "Copied to clipboard",
    text: props.ticket.name,
    icon: "check",
    iconClasses: "text-green-600",
  });
}
</script>
