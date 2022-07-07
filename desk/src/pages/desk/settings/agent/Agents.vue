<template>
	<div class="mt-[9px]">
		<ListManager
			class="px-[16px]"
			:options="{
				cache: ['Agents', 'Desk'],
				doctype: 'Agent',
				fields: [
					'user as email',
					'user.full_name as full_name',
					'group',
				],
				limit: 20,
				start_page: initialPage,
				route_query_pagination: true
			}"
		>
			<template #body="{ manager }">
				<AgentList :manager="manager" />
			</template>
		</ListManager>
		<AddNewAgentsDialog :show="showNewAgentDialog" @close="() => { showNewAgentDialog = false}" />
	</div>
</template>
<script>
import { inject, ref } from 'vue'
import AgentList from '@/components/desk/settings/agents/AgentList.vue'
import ListManager from '@/components/global/ListManager.vue'
import AddNewAgentsDialog from "@/components/desk/global/AddNewAgentsDialog.vue"

export default {
	name: 'Agents',
	components: {
		AgentList,
		ListManager,
		AddNewAgentsDialog
	},
	data() {
		return {
			initialPage: 1,
		}
	},
	setup() {
		const viewportWidth = inject('viewportWidth')
		const showNewAgentDialog =  ref(false)
		return { 
			viewportWidth,
			showNewAgentDialog
		}
	},
	activated() {
		this.$event.emit('set-selected-setting', 'Agents')
		this.$event.emit('show-top-panel-actions-settings', 'Agents')
		
		this.initialPage = parseInt(this.$route.query.page ? this.$route.query.page : 1)

		this.$event.on('show-new-agent-dialog', () => {
			console.log(this.showNewAgentDialog)
			this.showNewAgentDialog = true
		})
	},
	deactivated() {
		this.$event.off('show-new-agent-dialog')
	}
}
</script>