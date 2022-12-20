<template>
	<v-chart class="chart" :option="option" :theme="theme" />
</template>

<script>
import ECharts from "vue-echarts"
import "echarts/lib/chart/line"
import "echarts/lib/component/polar"
import theme from "./theme"
export default {
	name: "TicketSummaryChart",
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
		let dates = []
		let open = []
		let closed = []
		let replied = []
		let option = {
			title: {
				text: "Ticket Summary",
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
			legend: {
				data: [
					{ name: "Open", icon: "circle" },
					{ name: "Closed", icon: "circle" },
					{ name: "Replied", icon: "circle" },
				],
				right: "10%",
				top: "top",
			},
			xAxis: {
				type: "category",
				boundaryGap: false,
				data: dates,
			},
			yAxis: {
				type: "value",
			},
			series: [
				{
					name: "Open",
					type: "line",
					stack: "Total",
					data: open,
					lineStyle: {
						width: 3,
						color: "#61B2F9",
					},
				},
				{
					name: "Closed",
					type: "line",
					stack: "Total",
					data: closed,
					lineStyle: {
						width: 3,
						color: "#5FD8C4",
					},
				},
				{
					name: "Replied",
					type: "line",
					stack: "Total",
					data: replied,
					lineStyle: {
						width: 3,
						color: "#EEA4EF",
					},
				},
			],
		}
		return {
			dates,
			open,
			closed,
			replied,
			option,
			theme,
		}
	},
	methods: {
		getStatus() {
			this.$resources.ticketStatus.fetch()
		},
	},
	resources: {
		ticketStatus() {
			return {
				method: "frappedesk.api.dashboard.ticket_summary",
				params: {
					startDate: this.fromDate,
					endDate: this.toDate,
				},
				onSuccess: (res) => {
					this.dates.length = 0
					this.open.length = 0
					this.closed.length = 0
					this.replied.length = 0
					res.map((values) => {
						this.dates.push(values[0])
						this.open.push(values[1])
						this.closed.push(values[2])
						this.replied.push(values[3])
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
