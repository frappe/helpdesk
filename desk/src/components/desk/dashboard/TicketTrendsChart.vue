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
			console.log(newVal, Oldval, "trnd")
		},
		toDate(newVal, oldVal) {
			console.log(oldVal, newVal, "ddd")
		},
	},
	data() {
		let ticketCount = []
		let ticketMonth = []
		let option = {
			title: {
				text: "Ticket Trends",
				left: "5%",
			},
			tooltip: {
				trigger: "axis",
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
						width: 3					
					},
				},
			],
		}
		return {
			ticketCount,
			ticketMonth,
			option,
			theme,
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
	height: 50vh;
}
</style>
