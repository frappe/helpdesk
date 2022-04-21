<template>
	<div>
		<div v-if="agents">
			<AgentList :agents="agents" />
		</div>
	</div>
</template>
<script>
import { Input } from 'frappe-ui'
import AgentList from '@/components/desk/settings/agents/AgentList.vue'
import { inject, ref } from 'vue'

export default {
	name: 'Agents',
	components: {
		AgentList,
		Input
	},
	setup() {
		const viewportWidth = inject('viewportWidth')
		const selectedSetting = inject('selectedSetting')

		const showNewAgentDialog = ref(false)

		return { viewportWidth, selectedSetting, showNewAgentDialog }
	},
	resources: {
		agents() {
			return {
				method: 'frappedesk.api.agent.get_all',
				auto: true,
				fields: ['name']
			}
		}
	},
	activated() {
		this.selectedSetting = 'Agents'
	},
	deactivated() {

	},
	computed: {
		agents() {
			console.log(this.$resources.agents.data)
			return this.$resources.agents.data || null
		}
	},
	methods: {
		agentCreated(agent) {
			this.$resources.agents.fetch();
			this.showNewAgentDialog = false
		}
	},
}
</script>
