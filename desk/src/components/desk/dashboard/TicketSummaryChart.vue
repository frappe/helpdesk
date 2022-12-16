<template>
	<v-chart class="chart" :option="option" />
</template>

<script>
import ECharts from "vue-echarts"
import "echarts/lib/chart/line"
import "echarts/lib/component/polar"
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
			tooltip: {
				trigger: "axis",
			},
			legend: {
				data: ["Open", "Closed", "Replied"],
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
				},
				{
					name: "Closed",
					type: "line",
					stack: "Total",
					data: closed,
				},
				{
					name: "Replied",
					type: "line",
					stack: "Total",
					data: replied,
				},
			],
		}
		return {
			dates,
			open,
			closed,
			replied,
			option,
		}
	},
	methods: {
		getStatus() {
			console.log(this.$resources.ticketStatus.fetch())
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
	height: 50vh;
}
</style>
