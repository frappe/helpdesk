<template>
	<div class="block select-none rounded-[6px] py-[7px] px-[11px]" :class="selected ? 'bg-blue-50 hover:bg-blue-100' : 'hover:bg-gray-50'">
		<div
			v-if="agent"
			role="button"
			@pointerover="() => {toggleSelectBox = true}"
			@pointerleave="() => {toggleSelectBox = false}"
			class="flex items-center text-base"
		>
			<div 
				class="w-[37px] h-[14px] flex items-center"
			>
				<Input
					v-if="toggleSelectBox || selected"
					type="checkbox" 
					@click="$emit('toggleSelect')" 
					:checked="selected" 
					class="cursor-pointer mr-1 hover:visible" 
				/>
			</div>
			<router-link :to="`/frappedesk/settings/agents/${agent.name}`" class="w-full group flex items-center">
				<div class="sm:w-6/12 truncate pr-10">
					{{ agent.full_name }}
				</div>
				<div class="sm:w-4/12 truncate pr-10">
					{{ agent.email }}
				</div>
				<div class="sm:w-4/12 truncate pr-10">
					Roles
				</div>
				<div class="sm:w-4/12 truncate pr-10">
					{{ agent.group }}
				</div>
			</router-link>
		</div>
	</div>
</template>

<script>
import { ref } from 'vue'
import { Input, FeatherIcon } from 'frappe-ui'

export default {
	name: 'AgentListItem',
	props: ['agent', 'selected'],
	components: {
		Input,
		FeatherIcon,
	},
	setup() {
		const toggleSelectBox = ref(false)

		return {
			toggleSelectBox,
		}
	}
}
</script>