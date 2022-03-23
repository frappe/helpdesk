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

export default {
	name: 'SlaPolicySettings',
	inject: ['viewportWidth'],
	components: {
		SlaPolicyList,
		Input,
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
		this.$currentPage.set('SlaPolicySettings')
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
