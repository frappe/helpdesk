<template>
	<div class="flex flex-col">
		<div class="flex border-b h-[52px] px-[24px] shrink-0">
			<div class="grow my-auto text-[16px] font-semibold text-gray-900">
				Dashboard
			</div>
		</div>
		<div class="overflow-y-scroll h-full">
			<div class="mt-3.5 mr-8 ml-8">Welcome</div>
			<TicketStatusCards />
			<div class="ml-auto mr-6 w-48 mb-[20px]">
				<Datepicker
					v-model="date"
					range
					@update:modelValue="handleDate"
					:enable-time-picker="false"
				/>
			</div>
			<div class="grid grid-cols-2">
				<TicketTrendsChart
					class="w-50"
					:fromDate="fromDate"
					:toDate="toDate"
				/>
				<TicketSummaryChart
					class="w-50"
					:fromDate="fromDate"
					:toDate="toDate"
				/>
				<TicketTypeChart
					class="w-50"
					:fromDate="fromDate"
					:toDate="toDate"
				/>
				<CustomerSatisfactionChart
					class="w-50"
					:fromDate="fromDate"
					:toDate="toDate"
				/>
			</div>
			<SlaSummaryCards />
		</div>
	</div>
</template>

<script>
import TicketStatusCards from "@/components/desk/dashboard/TicketStatusCards.vue"
import TicketTrendsChart from "@/components/desk/dashboard/TicketTrendsChart.vue"
import Datepicker from "@vuepic/vue-datepicker"
import "@vuepic/vue-datepicker/dist/main.css"
import TicketTypeChart from "@//components/desk/dashboard/TicketTypeChart.vue"
import TicketSummaryChart from "@/components/desk/dashboard/TicketSummaryChart.vue"
import CustomerSatisfactionChart from "@/components/desk/dashboard/CustomerSatisfactionChart.vue"
import SlaSummaryCards from "@/components/desk/dashboard/SlaSummaryCards.vue"
export default {
	name: "Dashboard",
	components: {
		TicketStatusCards,
		TicketTrendsChart,
		Datepicker,
		TicketTypeChart,
		TicketSummaryChart,
		CustomerSatisfactionChart,
		SlaSummaryCards,
	},
	data() {
		let date = {}
		let fromDate = ""
		let toDate = ""
		return {
			date,
			fromDate,
			toDate,
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
			console.log(this.fromDate, this.toDate)
		},
	},
	beforeMount() {
		const startDate = new Date().setDate(new Date().getDate() - 7)
		const endDate = new Date()
		this.date.value = [startDate, endDate]
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

<style scoped></style>
