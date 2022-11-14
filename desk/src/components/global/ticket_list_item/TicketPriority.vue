<template>
	<div class="flex flex-row items-center space-x-1 text-gray-600">
		{{ value }}
	</div>
</template>

<script>
export default {
	name: "TicketPriority",
	props: {
		value: {
			type: String,
			required: true,
		},
	},
}
</script>
