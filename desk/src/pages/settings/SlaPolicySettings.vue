<template>
	<div>
		<div class="flow-root border-b pt-2 pb-3 pr-8">
			<div class="float-left ml-4">
				<div class="flex items-center space-x-4">
					<Input type="checkbox" value="" />
					<Button icon-left="plus" appearance="primary" @click="() => {}">Add Policy</Button>
				</div>
			</div>
			<div class="float-right">
				<Button icon-left="filter" type="white">Filter</Button>
			</div>
		</div>
		<div v-if="policies">
			<SlaPolicyList :policies="policies" />
		</div>
	</div>
</template>
<script>
import { Input } from 'frappe-ui'
import SlaPolicyList from '../../components/settings/policies/SlaPolicyList.vue'

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
