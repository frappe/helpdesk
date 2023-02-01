<template>
	<v-chart class="chart" :option="option" />
</template>

<script>
import ECharts from "vue-echarts"
import * as echarts from "echarts"
import "echarts/lib/chart/pie"
import "echarts/lib/component/polar"
import theme from "./theme"
export default {
	name: "CustomerSatisfactionChart",
	components: {
		"v-chart": ECharts,
	},
	props: {
		fromDate: {
			type: String,
			required: true,
		},
		toDate: {
			type: String,
			required: true,
		},
	},
	watch: {
		fromDate(newVal, Oldval) {
			console.log(newVal, Oldval)
		},
		toDate(newVal, oldVal) {
			console.log(oldVal, newVal)
		},
	},
	data() {
		let ticketCount = []
		let option = {
			title: {
				text: "Customer Satisfaction Feedback",
				textAlign: "left",
			},
			tooltip: {
				trigger: "item",
			},
			legend: {
				icon: "circle",
				orient: "horizontal",
				top: "bottom",
			},
			series: [
				{
					name: "Feedback Status",
					type: "pie",
					radius: "50%",
					data: ticketCount,
					color: [theme.green, theme.pink, theme.lightBlue],
					label: {
						formatter: "{b}: {c}",
					},
					emphasis: {
						itemStyle: {
							shadowBlur: 10,
							shadowOffsetX: 0,
							shadowColor: "rgba(0, 0, 0, 0.5)",
						},
					},
				},
			],
		}
		return {
			option,
			ticketCount,
		}
	},
	methods: {
		count() {
			this.$resources.getFeedbackStatusCount.fetch()
		},
	},
	resources: {
		getFeedbackStatusCount() {
			return {
				method: "frappedesk.api.dashboard.feedback_status",
				params: {
					dateFilter: [
						"creation",
						"between",
						[this.fromDate, this.toDate],
					],
				},
				onSuccess: (res) => {
					this.ticketCount.length = 0
					res.map((value) => {
						this.ticketCount.push(value)
					})
				},
				auto: true,
			}
		},
	},
}
</script>

<style scoped>
.chart {
	height: 30rem;
}
</style>
