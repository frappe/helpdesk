<template>
  <div class="flex-1 overflow-y-auto">
    <div
      v-if="analytics.loading"
      class="flex h-full flex-col items-center justify-center"
    >
      <LoadingIndicator :scale="8" />
    </div>
    <div
      v-else-if="analytics.data"
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
  </div>
</template>

<script setup lang="ts">
import { TicketSymbol } from "@/types";
import { createResource, LoadingIndicator } from "frappe-ui";
import { computed, inject, watch } from "vue";
import AnalyticsMetricCards from "./AnalyticsMetricCards.vue";
import ConversationSummary from "./ConversationSummary.vue";
import TicketTimeline from "./TicketTimeline.vue";

const ticket = inject(TicketSymbol)!;
const ticketId = computed(() => String(ticket.value.doc.name));

const analytics = createResource({
  url: "helpdesk.api.ticket_analytics.get_ticket_analytics",
  makeParams: () => ({ ticket: ticketId.value }),
  auto: true,
});

watch(ticketId, () => analytics.reload());
</script>
