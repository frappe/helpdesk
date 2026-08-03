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
      class="mx-auto flex w-full max-w-4xl flex-col gap-4 px-5 py-4"
    >
      <SlaTimeline
        :timeline="analytics.data.timeline"
        :has-sla="analytics.data.has_sla"
      />
      <AnalyticsMetricCards :metrics="analytics.data.metrics" />
      <div class="grid grid-cols-1 gap-3 lg:grid-cols-2">
        <ResponseGapChart :gaps="analytics.data.gaps" />
        <ConversationSummary :summary="analytics.data.summary" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { TicketSymbol } from "@/types";
import { createResource, LoadingIndicator } from "frappe-ui";
import { inject } from "vue";
import AnalyticsMetricCards from "./AnalyticsMetricCards.vue";
import ConversationSummary from "./ConversationSummary.vue";
import ResponseGapChart from "./ResponseGapChart.vue";
import SlaTimeline from "./SlaTimeline.vue";

const ticket = inject(TicketSymbol)!;
const ticketId = String(ticket.value.doc.name);

const analytics = createResource({
  url: "helpdesk.api.ticket_analytics.get_ticket_analytics",
  params: { ticket: ticketId },
  cache: ["ticket-analytics", ticketId],
  auto: true,
});
</script>
