<template>
  <VChart
    autoresize
    class="chart"
    :option="options"
    :init-options="initOptions"
    :theme="theme"
  />
</template>

<script setup lang="ts">
import { ref, toRefs, PropType } from "vue";
import { use } from "echarts/core";
import { SVGRenderer } from "echarts/renderers";
import { LineChart } from "echarts/charts";
import {
  GridComponent,
  LegendComponent,
  TitleComponent,
  TooltipComponent,
} from "echarts/components";
import VChart from "vue-echarts";
import { theme } from "./theme";

type InputData = {
  name: string;
  value: number;
};

type XAxisType = "category" | "value" | "time" | "log";

const props = defineProps({
  title: {
    type: String,
    required: true,
  },
  data: {
    type: Object as PropType<Array<InputData>>,
    required: true,
  },
  xAxisType: {
    type: String as PropType<XAxisType>,
    required: false,
    default: () => "category",
  },
});

const { data, title, xAxisType } = toRefs(props);

use([
  SVGRenderer,
  GridComponent,
  LegendComponent,
  LineChart,
  TitleComponent,
  TooltipComponent,
]);

const initOptions = {
  renderer: "svg",
};

const options = ref({
  grid: {
    bottom: "10%",
    top: "20%",
  },
  title: {
    text: title,
    textStyle: {
      color: "#374151",
      fontFamily: "Inter",
      fontSize: 14,
      fontWeight: 500,
    },
    left: "auto",
    right: "auto",
  },
  tooltip: {
    trigger: "item",
    formatter: "{b}<br />{c}",
  },
  xAxis: {
    type: xAxisType.value,
    data: data.value.map((d) => d.name),
  },
  yAxis: {},
  labelLine: {
    smooth: 0.2,
    length: 10,
    length2: 20,
  },
  series: [
    {
      name: title,
      type: "line",
      radius: "55%",
      center: ["50%", "60%"],
      data: data.value.map((d) => d.value),
      symbol: "circle",
      symbolSize: 6,
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: "rgba(0, 0, 0, 0.5)",
        },
      },
      areaStyle: {
        color: {
          type: "linear",
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            {
              offset: 0,
              color: theme.color[2],
            },
            {
              offset: 1,
              color: "rgba(0, 128, 255, 0)",
            },
          ],
        },
        opacity: 0.5,
      },
    },
  ],
});
</script>
