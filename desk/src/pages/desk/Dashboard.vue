<template>
	<div class="flex flex-col h-screen">
		<div class="flex border-b h-[52px] px-[18px] shrink-0">
			<div class="grow my-auto text-[16px] text-gray-900">
				Welcome, {{ user.agent ? user.agent.agent_name : user.user }}
			</div>
		</div>
		<div class="overflow-y-scroll h-full">
			<TicketStatusCards />
			<div class="mb-[20px] flex flex-row-reverse">
				<div class="w-48 mr-5">
					<Datepicker
						v-model="date"
						range
						@update:modelValue="handleDate"
						:enable-time-picker="false"
						format="MMM dd"
					/>
				</div>
			</div>
			<div class="grid grid-cols-2 ml-[18px]">
				<TicketTrendsChart
					class="min-w-[35rem]"
					:fromDate="fromDate"
					:toDate="toDate"
				/>
				<TicketSummaryChart
					class="min-w-[35rem]"
					:fromDate="fromDate"
					:toDate="toDate"
				/>
				<TicketTypeChart
					class="min-w-[35rem]"
					:fromDate="fromDate"
					:toDate="toDate"
				/>
				<CustomerSatisfactionChart
					class="min-w-[35rem]"
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
import CustomIcons from "@/components/desk/global/CustomIcons.vue"
import { onMounted, ref, inject } from "vue"
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
		const date = ref()
		onMounted(() => {
			const startDate = new Date().setDate(new Date().getDate() - 7)
			const endDate = new Date()
			date.value = [startDate, endDate]
		})

		const user = inject("user")

		return {
			date,
			user,
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

<style scoped></style>
