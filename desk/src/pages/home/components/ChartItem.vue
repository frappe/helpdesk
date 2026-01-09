<template>
  <div class="h-full w-full rounded border border-outline-gray-1">
    <AgentTicketsCard v-if="item.chart == 'agent_tickets'" :data="item.data" />
    <AvgFirstResponseCard
      v-if="item.chart == 'avg_first_response_time'"
      :data="item.data"
    />
    <AvgResolutionCard
      v-if="item.chart == 'avg_resolution_time'"
      :data="item.data"
    />
    <UpcomingSlaViolations
      v-if="item.chart == 'upcoming_sla_violations'"
      :data="item.data"
    />
    <RecentlyAssignedTickets
      v-if="item.chart == 'recently_assigned_tickets'"
      :data="item.data"
    />
    <RecentFeedback v-if="item.chart == 'recent_feedback'" :data="item.data" />
    <AvgTimeMetrics v-if="item.chart == 'avg_time_metrics'" :data="item.data" />
    <PendingTickets v-if="item.chart == 'pending_tickets'" :data="item.data" />
  </div>
</template>

<script setup lang="ts">
import AvgFirstResponseCard from "./AvgFirstResponseCard.vue";
import AvgResolutionCard from "./AvgResolutionCard.vue";
import AgentTicketsCard from "./AgentTicketsCard.vue";
import AvgTimeMetrics from "./AvgTimeMetrics.vue";
import RecentFeedback from "./RecentFeedback.vue";
import RecentlyAssignedTickets from "./RecentlyAssignedTickets.vue";
import UpcomingSlaViolations from "./UpcomingSlaViolations.vue";
import PendingTickets from "./PendingTickets.vue";

const props = defineProps({
  item: {
    type: Object,
    required: true,
  },
});
</script>
