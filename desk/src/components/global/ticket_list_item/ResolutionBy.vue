<template>
	<div
		class="text-gray-500 flex flex-row space-x-1 items-center"
		:class="{
			'text-red-500': $dayjs(value).fromNow().includes('ago'),
		}"
	>
		{{ value ? $dayjs.shortFormating($dayjs(value).fromNow(), true) : "" }}
	</div>
</template>

<script>
export default {
	name: "ResolutionBy",
	props: {
		ticket: {
			type: Object,
			required: true,
		},
	},
	computed: {
		value() {
			return this.ticket.resolution_by || null
		},
	},
}
</script>
