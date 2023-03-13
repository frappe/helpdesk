<template>
	<v-chart class="chart" :option="option" :theme="theme" />
</template>

<script>
import ECharts from "vue-echarts"
import * as echarts from "echarts"
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
	data() {
		let ticketType = []
		let ticketCount = []
		let option = {
			title: {
				text: "Tickets by Type",
				textAlign: "left",
			},
			tooltip: {
				trigger: "axis",
			},
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
					label: {
						show: true,
						position: "right",
						formatter: "{c}",
					},
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
				url: "frappedesk.api.dashboard.ticket_type",
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
