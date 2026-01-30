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
import { computed, onMounted, ref } from "vue";
import CardBase from "./CardBase.vue";
import { createResource } from "frappe-ui";

const props = defineProps({
  data: {
    type: Object,
    required: true,
  },
});

const currentDuration = ref("Last month");

const chartColor = {
  lineColor: "#5597F3",
  gradientColor: { start: "#abccfc", end: "rgba(229,240,254,0)" },
};

const chartConfig = computed(() => {
  const _data = getAgentTicketsResource.fetched
    ? getAgentTicketsResource.data
    : props.data;

  const _percentageChange = _data?.percentage_change;
  const total = _data?.total;
  const dates = _data?.data?.map((item: any) => item.date);
  const counts = _data?.data?.map((item: any) => item.count);

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
