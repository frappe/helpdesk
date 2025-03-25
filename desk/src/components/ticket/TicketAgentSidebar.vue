<template>
  <div class="flex w-[382px] flex-col justify-between border-l">
    <div
      class="flex h-10.5 cursor-copy items-center border-b px-5 py-2.5 text-lg font-medium text-ink-gray-9"
    >
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
      class="py-3 !px-6 !gap-3 text-base text-gray-600"
      :ticket="ticket"
    />
    <!-- ticket details -->
    <TicketAgentDetails :ticket="ticket" />
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
  if (typeof val.value === "object") {
    val.value = val.value.target?.value || null;
  }
  emit("update", val);
}
</script>
