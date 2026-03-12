<template>
  <div class="w-full h-full overflow-hidden">
    <CardBase
      :title="__('My Tickets')"
      :text="chartConfig.total"
      :chartData="chartConfig.data"
      :chartDates="chartConfig.dates"
      :currentDuration="currentDuration"
      :percentageChange="chartConfig.percentageChange"
      @changeDuration="changeDuration"
      :chartColor="chartColor"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, type PropType } from "vue";
import CardBase from "./CardBase.vue";
import { createResource } from "frappe-ui";

interface Data {
  percentage_change: number;
  total: number;
  data: { date: string; count: number }[];
}

const props = defineProps({
  data: {
    type: Object as PropType<Data>,
    required: true,
  },
});

const currentDuration = ref("Last month");

const chartColor = {
  lineColor: "#5597F3",
  gradientColor: { start: "#abccfc", end: "rgba(229,240,254,0)" },
};

const chartConfig = computed(() => {
  const _data: Data = getAgentTicketsResource.fetched
    ? getAgentTicketsResource.data
    : props.data;

  const _percentageChange = _data?.percentage_change || 0;
  const total = _data?.total || 0;
  const dates = _data?.data?.map((item) => item.date) || [];
  const counts = _data?.data?.map((item) => item.count) || [];

  const percentageChange = {
    icon: _percentageChange > 0 ? "arrow-up-right" : "arrow-down-left",
    value: _percentageChange > 0 ? `+${_percentageChange}` : _percentageChange,
    color: _percentageChange > 0 ? "text-red-600" : "text-green-600",
  };

  return {
    data: counts,
    percentageChange,
    total,
    counts,
    dates,
  };
});

const getAgentTicketsResource = createResource({
  url: "helpdesk.api.agent_home.agent_home.get_agent_tickets",
  type: "GET",
  makeParams: () => {
    return {
      period: currentDuration.value.toLowerCase(),
    };
  },
});

const changeDuration = (period: string) => {
  currentDuration.value = period;
  getAgentTicketsResource.submit();
};

onMounted(() => {
  if (!props.data?.data) {
    getAgentTicketsResource.submit();
  }
});
</script>
