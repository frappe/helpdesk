<template>
	<router-link
		:to="{
			path: `/helpdesk/tickets/${ticket.name}`,
		}"
		role="button"
		class="line-clamp-1 hover:text-gray-900 text-gray-600"
		:class="{
			'font-semibold text-gray-900': !(
				JSON.parse(ticket._seen) || []
			).includes(user.user),
		}"
	>
		{{ ticket.subject }}
	</router-link>
</template>

<script>
export default {
	name: "Subject",
	props: {
		ticket: {
			type: Object,
			required: true,
		},
	},
	inject: ["user"],
}
</script>
