<template>
  <div class="w-full h-full overflow-hidden">
    <CardBase
      :title="__('My Tickets')"
      :text="total"
      :chartConfig="chartConfig"
      :currentDuration="currentDuration"
      :percentageChange="percentageChange"
      @changeDuration="changeDuration"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import CardBase from "./CardBase.vue";
import { EChartsOption } from "echarts";
import { createResource } from "frappe-ui";

const props = defineProps({
  data: {
    type: Object,
    required: true,
  },
});

const currentDuration = ref("Last month");

const percentageChange = computed(() => {
  const _percentageChange = getAgentTicketsResource.fetched
    ? getAgentTicketsResource.data?.percentage_change
    : props.data?.percentage_change;
  return {
    icon: _percentageChange > 0 ? "arrow-up-right" : "arrow-down-left",
    value: _percentageChange > 0 ? `+${_percentageChange}` : _percentageChange,
    color: _percentageChange > 0 ? "text-red-600" : "text-green-600",
  };
});

const total = computed(() => {
  return getAgentTicketsResource.fetched
    ? getAgentTicketsResource.data?.total
    : props.data?.total;
});

const chartConfig = computed<EChartsOption>(() => {
  const isDataFetched = getAgentTicketsResource.fetched;
  const _data = isDataFetched
    ? getAgentTicketsResource.data?.data
    : props.data?.data;
  if (!_data) return {};

  const dates = _data.map((item) => item.date);
  const counts = _data.map((item) => item.count);
  const _percentageChange = isDataFetched
    ? getAgentTicketsResource.data?.percentage_change
    : props.data?.percentage_change;
  return {
    xAxis: {
      type: "category",
      data: dates,
      show: false,
    },
    yAxis: {
      type: "value",
      show: false,
    },
    series: [
      {
        data: counts,
        type: "line",
        symbol: "none",
      },
    ],
    color: _percentageChange > 0 ? "#F35555" : "#278F5E",
    grid: {
      left: 2,
      right: 2,
      top: 2,
      bottom: 2,
    },
  };
});

const getAgentTicketsResource = createResource({
  url: "helpdesk.api.agent_dashboard.get_agent_tickets",
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
