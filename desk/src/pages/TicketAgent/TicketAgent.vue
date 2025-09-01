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
import { TicketSymbol } from "@/types";
import { computed, provide, ref, watch } from "vue";
import { useRoute } from "vue-router";

const props = defineProps({
  ticketId: {
    type: String,
    required: true,
  },
});

const route = useRoute();

const currentTicketId = ref(props.ticketId);
const ticketComposable = ref(useTicket(currentTicketId.value));
const ticket = computed(() => ticketComposable.value.ticket);

// Watch for route parameter changes
watch(
  () => route.params.ticketId,
  (newTicketId) => {
    if (newTicketId && newTicketId !== currentTicketId.value) {
      currentTicketId.value = newTicketId as string;
      ticketComposable.value = useTicket(newTicketId as string);
    }
  },
  { immediate: true }
);

provide(TicketSymbol, ticket);
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
