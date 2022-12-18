<template>
	<v-chart class="chart" :option="option" />
</template>

<script>
import ECharts from "vue-echarts"
import "echarts/lib/chart/pie"
import "echarts/lib/component/polar"
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
				left: "5%",
			},
			color: ['#80FFA5', '#00DDFF', '#37A2FF', '#FF0087', '#FFBF00'],
			tooltip: {
				trigger: "item",
			},
			legend: {
				orient: "horizontal",
				top: "bottom",
			},
			series: [
				{
					name: "Feedback Status",
					type: "pie",
					radius: "50%",					
					data: ticketCount,
					color: ['#DE61F9', '#EEA4EF', '#37A2FF', '#5FD8C4'],
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
