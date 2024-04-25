<template>
  <div
    class="grid h-full place-items-center px-4 py-20 text-center text-lg text-gray-600"
  >
    <div class="space-y-2">
      <div>Invalid page or not permitted to access</div>
      <Button :route="{ name: 'TicketsAgent' }">
        <template #prefix><TicketIcon class="w-4" /></template>
        Tickets
      </Button>
    </div>
  </div>
</template>

<script setup>
import TicketIcon from "@/components/icons/TicketIcon.vue";
</script>
