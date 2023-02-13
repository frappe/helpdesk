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
			const a = this.agents.find((x) => x.name === this.agent);

			// Agent could be missing, corrupt or invalid. It is better to
			// have a fallback value, which in this case is an empty object.
			if (!a) return {};

			return a;
		},
	},
}
</script>
