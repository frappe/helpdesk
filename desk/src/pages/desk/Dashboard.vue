<template>
	<div class="flex flex-col h-screen">
		<div class="flex border-b h-[52px] px-[18px] shrink-0">
			<div class="grow my-auto text-[16px] text-gray-900">
				Welcome, {{ authStore.agent ? authStore.agent.agent_name : authStore.user }}
			</div>
		</div>
		<div class="overflow-y-scroll h-full">
			<TicketStatusCards class="mx-4 my-4" />
			<div class="grid grid-cols-2 gap-4 w-full px-[18px]">
				<TicketTrendsChart
					class="chart-card"
					:fromDate="fromDate"
					:toDate="toDate"
				/>
				<TicketSummaryChart
					class="chart-card"
					:fromDate="fromDate"
					:toDate="toDate"
				/>
				<TicketTypeChart
					class="chart-card"
					:fromDate="fromDate"
					:toDate="toDate"
				/>
				<CustomerSatisfactionChart
					class="chart-card"
					:fromDate="fromDate"
					:toDate="toDate"
				/>
			</div>
			<SlaSummaryCards />
		</div>
	</div>
</template>

<script>
import { onMounted, ref, inject } from "vue"
import TicketStatusCards from "@/components/desk/dashboard/TicketStatusCards.vue"
import TicketTrendsChart from "@/components/desk/dashboard/TicketTrendsChart.vue"
import TicketTypeChart from "@//components/desk/dashboard/TicketTypeChart.vue"
import TicketSummaryChart from "@/components/desk/dashboard/TicketSummaryChart.vue"
import CustomerSatisfactionChart from "@/components/desk/dashboard/CustomerSatisfactionChart.vue"
import SlaSummaryCards from "@/components/desk/dashboard/SlaSummaryCards.vue"
import CustomIcons from "@/components/desk/global/CustomIcons.vue"
import { useAuthStore } from "@/stores/auth"
export default {
	name: "Dashboard",
	components: {
		TicketStatusCards,
		TicketTrendsChart,
		TicketTypeChart,
		TicketSummaryChart,
		CustomerSatisfactionChart,
		SlaSummaryCards,
		CustomIcons,
	},

	data() {
		let fromDate = ""
		let toDate = ""

		return {
			fromDate,
			toDate,
		}
	},

	setup() {
		const authStore = useAuthStore()
		const date = ref()

		onMounted(() => {
			const startDate = new Date().setDate(new Date().getDate() - 7)
			const endDate = new Date()
			date.value = [startDate, endDate]
		})

		return {
			authStore,
			date,
		}
	},
	methods: {
		handleDate(modelData) {
			this.date.value = modelData
			this.fromDate = new Date(this.date.value[0]).toLocaleDateString(
				"en-IN",
				{
					year: "numeric",
					month: "2-digit",
					day: "2-digit",
				}
			)
			this.fromDate = this.fromDate.split("/").reverse().join("-")
			this.toDate = new Date(this.date.value[1]).toLocaleDateString(
				"en-IN",
				{
					year: "numeric",
					month: "2-digit",
					day: "2-digit",
				}
			)
			this.toDate = this.toDate.split("/").reverse().join("-")
		},
	},
	beforeMount() {
		const startDate = new Date().setDate(new Date().getDate() - 7)
		const endDate = new Date()
		this.fromDate = startDate
		this.fromDate = new Date(startDate).toLocaleDateString("en-IN", {
			year: "numeric",
			month: "2-digit",
			day: "2-digit",
		})
		this.fromDate = this.fromDate.split("/").reverse().join("-")
		this.toDate = endDate
		this.toDate = new Date(endDate).toLocaleDateString("en-IN", {
			year: "numeric",
			month: "2-digit",
			day: "2-digit",
		})
		this.toDate = this.toDate.split("/").reverse().join("-")
	},
}
</script>

<style>
.chart-card {
	@apply max-h-[400px] min-w-[535px] rounded-md border-gray-200 border shadow-sm p-5;
}
</style>
