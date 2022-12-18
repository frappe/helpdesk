<template>
	<v-chart class="chart" :option="option" :theme="theme" />
</template>

<script>
import ECharts from "vue-echarts"
import "echarts/lib/chart/bar"
import theme from "./theme"
export default {
	name: "TicketTypeChart",
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
			console.log(newVal, Oldval, "broooo")
		},
		toDate(newVal, oldVal) {
			console.log(oldVal, newVal, "todate")
		},
	},
	data() {
		let ticketType = []
		let ticketCount = []
		let option = {
			title: {
				text: "Tickets by Type",
				left: "5%",
			}, // color: ["#2D95F0", "#61B2F9", "#5FD8C4", "#f8bad0", "#EEA4EF", "#f2b3c9"],
			yAxis: {
				type: "category",
				data: ticketType,
			},
			xAxis: {
				type: "value",
			},
			series: [
				{
					data: ticketCount,
					type: "bar",
					itemStyle: {
						barBorderRadius: 5,
						barWidth: 5,
					},
				},
			],
		}
		return {
			option,
			ticketType,
			ticketCount,
			theme,
		}
	},
	methods: {
		count() {
			this.$resources.getTicketTypeCount.fetch()
		},
	},
	resources: {
		getTicketTypeCount() {
			return {
				method: "frappedesk.api.dashboard.ticket_type",
				params: {
					filters: [
						["creation", "between", [this.fromDate, this.toDate]],
					],
				},
				onSuccess: (res) => {
					this.ticketType.length = 0
					this.ticketCount.length = 0
					res.map((value) => {
						this.ticketCount.push(value.count)
						this.ticketType.push(value.ticket_type)
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
