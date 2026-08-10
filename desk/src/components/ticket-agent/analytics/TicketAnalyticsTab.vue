<template>
  <div class="flex-1 overflow-y-auto">
    <div
      v-if="analytics.data"
      class="mx-auto flex w-full max-w-6xl flex-col gap-4 px-5 py-4"
    >
      <TicketTimeline
        :timeline="analytics.data.timeline"
        :events="analytics.data.events"
      />
      <div class="grid items-start gap-4 lg:grid-cols-2">
        <ConversationSummary :summary="analytics.data.summary" />
        <AnalyticsMetricCards :metrics="analytics.data.metrics" />
      </div>
    </div>
    <div
      v-else-if="analytics.error"
      class="flex h-full flex-col items-center justify-center gap-3"
    >
      <p class="text-p-base text-ink-gray-6">
        {{ __("Failed to load analytics") }}
      </p>
      <Button :label="__('Retry')" @click="analytics.reload()" />
    </div>
    <div v-else class="flex h-full flex-col items-center justify-center">
      <LoadingIndicator :scale="8" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useTicket } from "@/composables/useTicket";
import { TicketSymbol } from "@/types";
import { Button, LoadingIndicator } from "frappe-ui";
import { computed, inject, watch } from "vue";
import AnalyticsMetricCards from "./AnalyticsMetricCards.vue";
import ConversationSummary from "./ConversationSummary.vue";
import TicketTimeline from "./TicketTimeline.vue";

const ticket = inject(TicketSymbol)!;
const ticketId = computed(() => String(ticket.value.doc.name));
const analytics = computed(() => useTicket(ticketId.value).analytics);

// status and priority changes rewrite the SLA picture (hold, due dates), so
// the analytics must refetch, not just on ticket switch
watch(
  () => [ticketId.value, ticket.value.doc.status, ticket.value.doc.priority],
  () => analytics.value.reload(),
  { immediate: true }
);
</script>
