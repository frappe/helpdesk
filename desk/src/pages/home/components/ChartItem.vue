<template>
  <div class="h-full w-full rounded border border-outline-gray-1">
    <AgentTicketsCard v-if="item.chart == 'agent_tickets'" :data="item.data" />
    <AvgTimeCard
      v-if="item.chart == 'avg_first_response_time'"
      :title="__('Average First Response')"
      api-url="helpdesk.api.agent_home.agent_home.get_avg_first_response_time"
      :data="item.data"
      :chart-color="{
        lineColor: '#F35555',
        gradientColor: { start: '#ee9d9f', end: 'rgba(251,232,233,0)' },
      }"
    />
    <AvgTimeCard
      v-if="item.chart == 'avg_resolution_time'"
      :title="__('Average Resolution')"
      api-url="helpdesk.api.agent_home.agent_home.get_avg_resolution_time"
      :data="item.data"
      :chart-color="{
        lineColor: '#7263E8',
        gradientColor: { start: '#a093ee', end: 'rgba(239, 237, 252,0)' },
      }"
    />
    <RecentFeedback v-if="item.chart == 'recent_feedback'" :data="item.data" />
    <AvgTimeMetrics v-if="item.chart == 'avg_time_metrics'" :data="item.data" />
    <PendingTickets v-if="item.chart == 'pending_tickets'" :data="item.data" />
  </div>
</template>

<script setup lang="ts">
import { type PropType } from "vue";
import AvgTimeCard from "./AvgTimeCard.vue";
import AgentTicketsCard from "./AgentTicketsCard.vue";
import AvgTimeMetrics from "./AvgTimeMetrics.vue";
import RecentFeedback from "./RecentFeedback.vue";
import PendingTickets from "./PendingTickets.vue";
import { __ } from "@/translation";

interface Item {
  chart: string;
  data: any;
}

const props = defineProps({
  item: {
    type: Object as PropType<Item>,
    required: true,
  },
});
</script>
