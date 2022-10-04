<template>
	<div class="flex flex-row w-full h-full">
		<AgentInfo
			class="shrink-0 border-r border-[#F4F5F6]"
			:agent="agentId"
		/>
		<AgentRelatedInfo class="grow" :agent="agentId" />
	</div>
</template>

<script>
import AgentInfo from "@/components/desk/settings/agents/AgentInfo.vue"
import AgentRelatedInfo from "@/components/desk/settings/agents/AgentRelatedInfo.vue"

export default {
	name: "Agent",
	props: ["agentId"],
	components: {
		AgentInfo,
		AgentRelatedInfo,
	},
	setup() {},
	mounted() {
		this.$event.emit("set-selected-setting", "Agents")
		this.$event.emit("show-top-panel-actions-settings", "Agent")
	},
}
</script>
