<template>
	<v-chart class="chart" :option="option" autoresize />
</template>

<script setup lang="ts">
import { ref, toRefs, PropType } from "vue";
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { LineChart } from "echarts/charts";
import {
	GridComponent,
	LegendComponent,
	TitleComponent,
	TooltipComponent,
} from "echarts/components";
import VChart from "vue-echarts";

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
	CanvasRenderer,
	GridComponent,
	LegendComponent,
	LineChart,
	TitleComponent,
	TooltipComponent,
]);

const option = ref({
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
