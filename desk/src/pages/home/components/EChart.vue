<template>
  <div ref="chartDiv" class="h-full w-full"></div>
</template>

<script setup lang="ts">
import { EChartsOption, init } from "echarts";
import { debounce } from "frappe-ui";
import { onBeforeUnmount, onMounted, ref, watch } from "vue";

const props = defineProps<{
  options: EChartsOption;
  events?: {
    click: (params: any) => void;
  };
}>();

let chart: echarts.ECharts;
const chartDiv = ref<HTMLDivElement>();

onMounted(() => {
  if (!chartDiv.value) return;

  chart = init(chartDiv.value, "light", { renderer: "svg" });
  chart.setOption({ ...props.options }, true);

  if (props.events?.click) {
    chart.on("click", props.events.click);
  }

  const resizeDebounce = debounce(() => {
    chart.resize({
      animation: {
        duration: 300,
      },
    });
  }, 250);

  let resizeObserver = new ResizeObserver(resizeDebounce);
  setTimeout(() => resizeObserver.observe(chartDiv.value!), 500);
  onBeforeUnmount(() => resizeObserver.unobserve(chartDiv.value!));
});

watch(
  () => props.options,
  (newOptions) => {
    if (chart) {
      chart.setOption(newOptions, true);
    }
  },
  { deep: true }
);
</script>
