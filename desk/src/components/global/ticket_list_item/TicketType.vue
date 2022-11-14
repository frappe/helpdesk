<template>
	<div v-if="value" class="text-gray-600">
		{{ value }}
	</div>
</template>

<script>
export default {
	name: "TicketType",
	props: {
		value: {
			type: String,
			required: true,
		},
	},
}
</script>
