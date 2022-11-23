<template>
	<div
		class="flex flex-row space-x-1 items-center"
		:class="{
			'text-red-500': overdue,
			'text-gray-500': !overdue,
		}"
	>
		{{ value }}
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
	data() {
		return {
			overdue: false,
		}
	},
	computed: {
		value() {
			if (!this.ticket.resolution_by) return null
			if (this.ticket.status == "Replied") return ""

			if (["Resolved", "Closed"].includes(this.ticket.status)) {
				if (this.ticket.agreement_status == "Overdue") {
					this.overdue = true
					return "Overdue"
				} else {
					this.overdue = false
					return "Fulfiled"
				}
			}
			this.overdue = this.$dayjs(this.ticket.resolution_by)
				.fromNow()
				.includes("ago")

			return this.$dayjs.shortFormating(
				this.$dayjs(this.ticket.resolution_by).fromNow(),
				false
			)
		},
	},
}
</script>
