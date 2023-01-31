<template>
	<div class="grid grid-cols-4 gap-4">
		<div
			class="flex flex-row card h-16 p-4 rounded-md justify-between items-center"
		>
			<div class="flex flex-row gap-2">
				<div class="text-xl text-red-500">Due Today</div>
			</div>
			<span class="text-7xl text-gray-700 font-medium">
				{{ dueToday != null ? dueToday : 0 }}
			</span>
		</div>
		<div
			class="flex flex-row card h-16 p-4 justify-between items-center"
		>
			<div class="flex flex-row gap-2">
				<div class="text-xl font-normal text-gray-600">Unresolved</div>
			</div>
			<span class="text-7xl text-gray-700 font-medium">
				{{ open + replied }}
			</span>
		</div>
		<div
			class="flex flex-row h-16 p-4 card justify-between items-center"
		>
			<div class="flex flex-row gap-2">
				<div class="text-xl text-gray-600 font-normal">Open</div>
			</div>
			<span class="text-7xl text-gray-700 font-medium">
				{{ open != null ? open : 0 }}
			</span>
		</div>

		<div
			class="flex flex-row h-16 p-4 card justify-between items-center"
		>
			<div class="flex flex-row gap-2">
				<div class="text-xl text-gray-600 font-normal">Replied</div>
			</div>
			<span class="text-7xl text-gray-700 font-medium">
				{{ replied != null ? replied : 0 }}
			</span>
		</div>
	</div>
</template>

<script>
import CustomIcons from "@/components/desk/global/CustomIcons.vue"
export default {
	name: "TicketStatusCards",
	components: {
		CustomIcons,
	},
	computed: {
		dueToday() {
			let value = null
			let ticketStatusValue = this.$resources.getTicketStatusCount.data
			ticketStatusValue?.map((res) => {
				if (res.map == "Open" && res.resolution_by == new Date()) {
					value = res.count
				} else {
					value = 0
				}
			})
			return value
		},
		resolved() {
			let value = null
			let ticketStatusValue = this.$resources.getTicketStatusCount.data
			ticketStatusValue?.map((res) => {
				if (res.status == "Resolved") {
					value = res.count
				}
			})
			return value
		},
		replied() {
			let value = null
			let ticketStatusValue = this.$resources.getTicketStatusCount.data
			ticketStatusValue?.map((res) => {
				if (res.status == "Replied") {
					value = res.count
				}
			})
			return value
		},
		open() {
			let value = null
			let ticketStatusValue = this.$resources.getTicketStatusCount.data
			ticketStatusValue?.map((res) => {
				if (res.status == "Open") {
					value = res.count
				}
			})
			return value
		},
		closed() {
			let value = null
			let ticketStatusValue = this.$resources.getTicketStatusCount.data
			ticketStatusValue?.map((res) => {
				if (res.status == "Closed") {
					value = res.count
				}
			})
			return value
		},
	},
	resources: {
		getTicketStatusCount() {
			return {
				method: "frappedesk.api.dashboard.ticket_status",
				auto: true,
			}
		},
	},
}
</script>

<style scoped>
.card {
	@apply rounded-md border-gray-200 border shadow-sm;
}
</style>
