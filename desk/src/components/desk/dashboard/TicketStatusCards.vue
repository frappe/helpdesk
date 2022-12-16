<template>
	<div class="grid grid-cols-4 gap-4 mt-8 ml-8 mb-8 mr-6">
		<div class="box-border h-[86px] p-4 border-2 rounded-md">
			<div>Due Today</div>
			<div>
				{{ dueToday != null ? dueToday : 0 }}
			</div>
		</div>
		<div class="box-border h-[86px] p-4 border-2 rounded-md">
			<div>Unresolved</div>
			<div>
				{{ open != null ? open : 0 }}
			</div>
		</div>
		<div class="box-border h-[86px] p-4 border-2 rounded-md">
			<div>Open</div>
			<div>
				{{ open != null ? open : 0 }}
			</div>
		</div>
		<div class="box-border h-[86px] p-4 border-2 rounded-md">
			<div>Replied</div>
			<div>
				{{ replied != null ? replied : 0 }}
			</div>
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
			let ticket_status_value = this.$resources.getTicketStatusCount.data
			ticket_status_value?.map((res) => {
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
			let ticket_status_value = this.$resources.getTicketStatusCount.data
			ticket_status_value?.map((res) => {
				if (res.status == "Resolved") {
					value = res.count
				}
			})
			return value
		},
		replied() {
			let value = null
			let ticket_status_value = this.$resources.getTicketStatusCount.data
			ticket_status_value?.map((res) => {
				if (res.status == "Replied") {
					value = res.count
				}
			})
			return value
		},
		open() {
			let value = null
			let ticket_status_value = this.$resources.getTicketStatusCount.data
			ticket_status_value?.map((res) => {
				if (res.status == "Open") {
					value = res.count
				}
			})
			return value
		},
		closed() {
			let value = null
			let ticket_status_value = this.$resources.getTicketStatusCount.data
			ticket_status_value?.map((res) => {
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