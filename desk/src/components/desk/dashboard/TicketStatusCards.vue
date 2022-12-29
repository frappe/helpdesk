<template>
	<div class="grid grid-cols-4 gap-4 mt-8 ml-8 mb-8 mr-6">
		<div class="box-border h-24 p-4 border-2 rounded-md">
			<div class="flex flex-row gap-2">
				<div class="text-xl text-red-500">Due Today</div>
				<CustomIcons
					name="corner-up-right"
					class="h-3 relative top-1.5"
				/>
			</div>
			<span class="text-[36px] font-bold">
				{{ dueToday != null ? dueToday : 0 }}
			</span>
		</div>
		<div class="box-border h-24 p-4 border-2 rounded-md">
			<div class="flex flex-row gap-2">
				<div class="text-xl font-normal text-[#687178]">Unresolved</div>
				<CustomIcons
					name="corner-up-right"
					class="h-3 relative top-1.5"
				/>
			</div>
			<span class="text-[36px] text-[#505A62] font-medium">
				{{ open + replied }}
			</span>
		</div>
		<div class="box-border h-24 p-4 border-2 rounded-md">
			<div class="flex flex-row gap-2">
				<div class="text-xl text-[#687178] font-normal">Open</div>
				<CustomIcons
					name="corner-up-right"
					class="h-3 relative top-1.5"
				/>
			</div>
			<span class="text-[36px] text-[#505A62] font-medium">
				{{ open != null ? open : 0 }}
			</span>
		</div>

		<div class="box-border h-24 p-4 border-2 rounded-md">
			<div class="flex flex-row gap-2">
				<div class="text-xl text-[#687178] font-normal">Replied</div>
				<CustomIcons
					name="corner-up-right"
					class="h-3 relative top-1.5"
				/>
			</div>
			<span class="text-[36px] text-[#505A62] font-medium">
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
