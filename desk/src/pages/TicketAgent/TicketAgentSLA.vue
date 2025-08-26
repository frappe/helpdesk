<template>
  <!-- Teleport to App Header -->
  <teleport to="#app-header">
    <div
      class="flex items-center mx-5 md:mr-0 text-p-sm gap-3 text-[14px] mb-[13px]"
    >
      <!-- Source -->
      <div class="flex items-center gap-1">
        <p>#{{ ticket.doc.name }}</p>
        <!-- Via Email -->
        <div
          v-if="!ticket.doc.via_customer_portal"
          class="text-ink-gray-4 flex items-center"
        >
          <span class="text-ink-gray-4 mr-[6px]">via</span>
          <EmailIcon class="size-4 inline-block mr-1" />
          <span class="font-medium">Email</span>
        </div>
        <!-- Via Portal -->
        <div v-else class="text-ink-gray-4 flex items-center">
          <span class="text-ink-gray-4 mr-[6px]">via</span>
          <GlobeIcon class="size-4 inline-block mr-1" />
          <span class="font-medium">Portal</span>
        </div>
      </div>
      <!-- divider -->
      <div class="border-l border-outline-gray-2 h-[13px]" />
      <!-- First Response -->
      <div class="flex items-center gap-1">
        <span>First Response</span>
        <Badge label="Due in 22h 30m" variant="subtle" theme="orange" />
      </div>
      <!-- divider -->
      <div class="border-l border-outline-gray-2 h-[13px]" />
      <!-- Resolution by -->
      <div class="flex items-center gap-1">
        <span>Resolution </span>
        <Badge label="Due in 3d 2h" class="text-[#4F3DA1] bg-[#EEE8FF]" />
      </div>
    </div>
  </teleport>
</template>

<script setup lang="ts">
import { useTicket } from "@/composables/useTicket";

const props = defineProps({
  ticketId: {
    type: String,
    required: true,
  },
});

const ticket = useTicket(props.ticketId);
</script>

<style scoped></style>
