<template>
	<div>
		<div class="flow-root border-b pt-2 pb-3 pr-8">
			<div class="float-left ml-4">
				<div class="flex items-center space-x-4">
					<Input type="checkbox" value="" />
					<Button icon-left="plus" appearance="primary" @click="() => {showNewAgentDialog = true}">Add Agent</Button>
				</div>
			</div>
			<div class="float-right">
				<Button icon-left="filter" type="white">Filter</Button>
			</div>
		</div>
		<div v-if="agents">
			<AgentList :agents="agents" />
		</div>
		<NewAgentDialog v-model="showNewAgentDialog" @agent-created="(agent) => {agentCreated(agent)}"/>
	</div>
</template>
<script>
import { Input } from 'frappe-ui'
import AgentList from '@/components/settings/agents/AgentList.vue'
import NewAgentDialog from '@/components/global/NewAgenDialog.vue'

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
		this.$currentPage.set('AgentsSettings')
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
