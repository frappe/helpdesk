<template>
	<v-chart class="chart" :option="option" :theme="theme" />
</template>

<script>
import ECharts from "vue-echarts"
import echarts from "echarts"
import "echarts/lib/chart/line"
import "echarts/lib/component/polar"
import theme from "./theme"
export default {
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
		let ticketMonth = []
		return {
			theme,
			option: {
				title: {
					text: "Ticket Trends (Count)",
					left: "5%",
				},
				// color: ["#2D95F0", "#61B2F9", "#5FD8C4", "#f8bad0", "#EEA4EF", "#f2b3c9"],
				tooltip: {
					trigger: "axis",
					axisPointer: {
						type: "cross",
						label: {
							backgroundColor: "#6a7985",
						},
					},
				},
				xAxis: {
					type: "category",
					boundaryGap: false,
					data: ticketMonth,
				},
				yAxis: {
					type: "value",
				},
				series: [
					{
						name: "Ticket Count",
						data: ticketCount,
						type: "line",
						stack: "total",
						showSymbol: false,
						lineStyle: {
							width: 3,
							color: "#61B2F9",
						},
					},
				],
				color: theme.color,
			},
			ticketCount,
			ticketMonth,
		}
	},
	methods: {
		count() {
			this.$resources.getTicketCount.fetch()
		},
	},
	resources: {
		getTicketCount() {
			return {
				method: "frappedesk.api.dashboard.get_ticket_count",
				params: {
					filters: [
						["creation", "between", [this.fromDate, this.toDate]],
					],
				},
				onSuccess: (res) => {
					let holder = {}
					res.map((value) => {
						if (
							holder.hasOwnProperty(
								new Date(value.creation).toLocaleDateString(
									"en-IN",
									{ day: "2-digit", month: "2-digit" }
								)
							)
						) {
							holder[
								new Date(value.creation).toLocaleDateString(
									"en-IN",
									{ day: "2-digit", month: "2-digit" }
								)
							] =
								holder[
									new Date(value.creation).toLocaleDateString(
										"en-IN",
										{ day: "2-digit", month: "2-digit" }
									)
								] + value.count
						} else {
							holder[
								new Date(value.creation).toLocaleDateString(
									"en-IN",
									{ day: "2-digit", month: "2-digit" }
								)
							] = value.count
						}
					})
					var arr = []
					for (var prop in holder) {
						arr.push({ creation: prop, count: holder[prop] })
					}
					this.ticketCount.length = 0
					this.ticketMonth.length = 0
					arr.map((res) => {
						this.ticketCount.push(res.count)
						this.ticketMonth.push(res.creation)
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
