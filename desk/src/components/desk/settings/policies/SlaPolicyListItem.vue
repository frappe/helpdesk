<template>
	<div class="block py-3 hover:bg-gray-50 border-b text-base">
		<router-link 
			v-if="policy"
			class="group flex items-center justify-between sm:justify-start font-light pl-4 pr-8 space-x-2"
			:to="`/frappedesk/settings/sla/${policy.name}`"
		>
			<div>
				<Input type="checkbox" value="" />
			</div>
			<div class="sm:w-3/12">
				{{ policy.name }}
			</div>
			<div class="sm:w-2/12">
				{{ policy.default_service_level_agreement ? "Default" : ""}}
			</div>
			<div class="sm:w-2/12">
				<CustomSwitch v-model="policy.enabled" />
			</div>
		</router-link>
	</div>
</template>

<script>
import { Input, FeatherIcon } from 'frappe-ui'
import CustomSwitch from '@/components/global/CustomSwitch.vue'
import { onMounted, ref, watch } from 'vue'

export default {
	name: 'SlaPolicyListItem',
	props: ['policy'],
	components: {
		Input,
		FeatherIcon,
		CustomSwitch
	},
	setup(props) {
		const enabled = ref(false)

		watch(enabled, async (newVal, oldVal) => {
			console.log(`enabled switched to ${newVal}`)
		})
		
		onMounted(() => {
			enabled.value = props.policy.enabled
		})

		return { enabled }
    },
}
</script>

<style>

</style>