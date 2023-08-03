<template>
  <v-chart
    autoresize
    class="chart"
    :init-options="initOptions"
    :option="options"
    :theme="theme"
  />
</template>

<script setup lang="ts">
import { ref, toRefs, PropType } from "vue";
import { use } from "echarts/core";
import { SVGRenderer } from "echarts/renderers";
import { PieChart } from "echarts/charts";
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
} from "echarts/components";
import VChart from "vue-echarts";
import { sortBy } from "lodash";
import { theme } from "./theme";

type InputData = {
  name: string;
  value: number;
};

const props = defineProps({
  title: {
    type: String,
    required: true,
  },
  data: {
    type: Object as PropType<Array<InputData>>,
    required: true,
  },
});

const { title, data } = toRefs(props);

use([SVGRenderer, PieChart, TitleComponent, TooltipComponent, LegendComponent]);

const initOptions = {
  renderer: "svg",
};

const options = ref({
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
    formatter: "{c} ({d}%)",
  },
  labelLine: {
    smooth: 0.2,
    length: 10,
    length2: 20,
  },
  series: [
    {
      name: title,
      type: "pie",
      radius: "55%",
      center: ["50%", "60%"],
      data: sortBy(data.value, (o: InputData) => o.value),
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: "rgba(0, 0, 0, 0.5)",
        },
      },
    },
  ],
});
</script>
