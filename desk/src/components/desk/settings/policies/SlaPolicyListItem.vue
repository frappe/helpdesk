<template>
	<div class="block py-3 hover:bg-gray-50 border-b text-base">
		<router-link 
			v-if="policy"
			class="group flex items-center justify-between sm:justify-start font-light pl-4 pr-8 space-x-2"
			:to="`/policys/${policy.name}`"
		>
			<div>
				<Input type="checkbox" value="" />
			</div>
			<div class="sm:w-3/12">
				{{ policy.name }}
			</div>
			<div class="sm:w-3/12">
				{{ policy.default_service_level_agreement ? "Default" : ""}}
			</div>
			<div class="sm:w-1/12">
				<Switch
					v-model="enabled"
					:class="policy.enabled ? 'bg-blue-500' : 'bg-slate-300'"
					class="relative inline-flex items-center h-6 rounded-full w-11"
				>
					<span class="sr-only">Enable notifications</span>
					<span
						:class="policy.enabled ? 'translate-x-6' : 'translate-x-1'"
						class="inline-block w-4 h-4 transform bg-white rounded-full"
					/>
				</Switch>
			</div>
		</router-link>
	</div>
</template>

<script>
import { Input, FeatherIcon } from 'frappe-ui'
import { Switch } from '@headlessui/vue'
import { onMounted, ref, watch } from 'vue'

export default {
	name: 'SlaPolicyListItem',
	props: ['policy'],
	components: {
		Input,
		FeatherIcon,
		Switch
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