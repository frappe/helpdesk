<template>
	<div class="flex flex-col">
		<div class="flex border-b h-[52px] px-[24px] shrink-0">
			<div class="grow my-auto text-[16px] font-semibold text-gray-900">
				Dashboard
			</div>
		</div>
		<div class="overflow-y-scroll h-full">
			<div class="mt-3.5 mr-8 ml-8">Welcome {{ user }}</div>
			<TicketStatusCards />
		</div>
	</div>
</template>

<script>
import TicketStatusCards from "@/components/desk/dashboard/TicketStatusCards.vue"
export default {
	name: "Dashboard",
	components: {
		TicketStatusCards,
	},
}
</script>

<style scoped></style>
