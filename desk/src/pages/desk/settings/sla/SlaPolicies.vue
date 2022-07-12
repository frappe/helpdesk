<template>
	<div class="mt-[9px]">
		<ListManager
			class="px-[16px]"
			:options="{
				cache: ['Service Level Agreement', 'Settings'],
				doctype: 'Service Level Agreement',
				fields: [
					'name',
					'default_service_level_agreement',
					'enabled'
				],
				limit: 20,
				start_page: initialPage,
				route_query_pagination: true
			}"
		>
			<template #body="{ manager }">
				<SlaPolicyList :manager="manager" />
			</template>
		</ListManager>
	</div>
</template>
<script>
import { inject } from 'vue'
import ListManager from '@/components/global/ListManager.vue'
import SlaPolicyList from '@/components/desk/settings/policies/SlaPolicyList.vue'

export default {
	name: 'SlaPolicies',
	components: {
		SlaPolicyList,
		ListManager,
	},
	setup() {
		const viewportWidth = inject('viewportWidth')
		
		return { 
			viewportWidth 
		}
	},
	data() {
		return {
			initialPage: 1
		}
	},
	mounted() {
		this.$event.emit('set-selected-setting', 'Support Policies')
		this.$event.emit('show-top-panel-actions-settings', 'Support Policies')
	},
}
</script>
