<template>
	<div>
		<div v-if="policies">
			<SlaPolicyList :policies="policies" />
		</div>
	</div>
</template>
<script>
import { Input } from 'frappe-ui'
import SlaPolicyList from '@/components/desk/settings/policies/SlaPolicyList.vue'
import { inject } from 'vue'

export default {
	name: 'SlaPolicies',
	components: {
		SlaPolicyList,
		Input,
	},
	setup() {
		const viewportWidth = inject('viewportWidth')
		const selectedSetting = inject('selectedSetting')
		
		return { viewportWidth, selectedSetting }
	},
	resources: {
		policies() {
			return {
				method: 'frappe.client.get_list',
				params: {
					doctype: "Service Level Agreement",
					fields: ["*"]
				},
				auto: true,
			}
		}
	},
	activated() {
		this.selectedSetting = 'Support Policies'
	},
	deactivated() {

	},
	computed: {
		policies() {
			console.log(this.$resources.policies.data)
			return this.$resources.policies.data || null
		}
	},
}
</script>
