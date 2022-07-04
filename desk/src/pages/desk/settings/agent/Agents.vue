<template>
	<div class="mt-[9px]">
		<ListManager
			class="px-[16px]"
			:options="{
				cache: ['Agents', 'Desk'],
				doctype: 'Agent',
				fields: [
					'user.full_name',
					'user as email',
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
	</div>
</template>
<script>
import { inject } from 'vue'
import AgentList from '@/components/desk/settings/agents/AgentList.vue'
import ListManager from '@/components/global/ListManager.vue'

export default {
	name: 'Agents',
	components: {
		AgentList,
		ListManager
	},
	data() {
		return {
			initialPage: 1
		}
	},
	setup() {
		const viewportWidth = inject('viewportWidth')
		return { 
			viewportWidth 
		}
	},
	activated() {
		this.$event.emit('set-selected-setting', 'Agents')
		this.initialPage = parseInt(this.$route.query.page ? this.$route.query.page : 1)
	},
}
</script>
