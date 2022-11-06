<template>
	<Avatar size="sm" :imageURL="agent.user_image" :label="agent.agent_name" />
</template>

<script>
import { Avatar } from "frappe-ui"
import { inject } from "vue"

export default {
	name: "AgentAvatar",
	props: ["agent"],
	components: {
		Avatar,
	},
	setup() {
		const agents = inject("agents")
		return {
			agents,
		}
	},
	computed: {
		agent() {
			return this.agents.find((x) => x.name === this.agent)
		},
	},
}
</script>
