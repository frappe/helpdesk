<template>
	<div>
		<div v-if="agents">
			<AgentList :agents="agents" />
		</div>
		<NewAgentDialog v-model="showNewAgentDialog" @agent-created="(agent) => {agentCreated(agent)}"/>
	</div>
</template>
<script>
import { Input } from 'frappe-ui'
import AgentList from '@/components/desk/settings/agents/AgentList.vue'
import NewAgentDialog from '@/components/desk/global/NewAgenDialog.vue'

export default {
	name: 'AgentSettings',
	inject: ['viewportWidth'],
	components: {
		AgentList,
		Input,
		NewAgentDialog
	},
	data() {
		return {
			showNewAgentDialog: false
		}
	},
	resources: {
		agents() {
			return {
				method: 'helpdesk.api.agent.get_all',
				auto: true,
				fields: ['name']
			}
		}
	},
	activated() {
		this.$currentPage.set('AgentSettings')
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
	}
}
</script>
