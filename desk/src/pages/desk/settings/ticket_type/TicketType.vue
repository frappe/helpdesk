<template>
	<div class="flex flex-col">
		<TicketTypeInfo :ticketTypeId="ticketTypeId" />
	</div>
</template>

<script>
import TicketTypeInfo from "@/components/desk/settings/ticket_types/TicketTypeInfo.vue"
export default {
	name: "TicketType",
	props: ["ticketTypeId"],
	components: {
		TicketTypeInfo,
	},
	mounted() {
		this.$event.emit("set-selected-setting", "Ticket Types")
	},
}
</script>
