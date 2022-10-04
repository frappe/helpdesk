<template>
	<div class="pt-[8px]">
		<div v-for="(activity, index) in activities" :key="activity.name">
			<ActivityCard
				:activity="activity"
				:isLast="index == activities.length - 1"
			/>
		</div>
	</div>
</template>

<script>
import ActivityCard from "@/components/desk/ticket/ActivityCard.vue"

export default {
	props: ["ticketId"],
	components: {
		ActivityCard,
	},
	computed: {
		activities() {
			return this.$resources.activities.data || null
		},
	},
	mounted() {
		this.$socket.on("list_update", (data) => {
			if (
				data["doctype"] == "Ticket Activity" &&
				data["name"].split("-")[1] == this.ticketId
			) {
				this.$resources.activities.fetch()
			}
		})
	},
	unmounted() {
		this.$socket.off("list_update")
	},
	resources: {
		activities() {
			return {
				cache: ["Activities", "Info Panel", this.ticketId],
				method: "frappedesk.api.ticket.activities",
				params: {
					name: this.ticketId,
				},
				auto: true,
			}
		},
	},
}
</script>

<style></style>
