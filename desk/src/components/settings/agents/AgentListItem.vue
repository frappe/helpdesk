<template>
	<div class="block py-4 hover:bg-gray-50 border-b text-base">
		<router-link 
			v-if="agent"
			class="group flex items-center justify-between sm:justify-start font-light pl-4 pr-8 space-x-2"
            :to="`/agents/${agent.name}`"
		>
			<div
				class="mr-4"
			>
				<Input type="checkbox" value="" />
			</div>
			<div class="sm:w-4/12">
				{{ agent.agent_name }}
			</div>
			<div class="sm:w-4/12">
                {{ agent.name }}
			</div>
			<div class="sm:w-4/12 truncate">
                {{ agentRoles }}
			</div>
		</router-link>
	</div>
</template>

<script>
import { Input, FeatherIcon } from 'frappe-ui'

export default {
	name: 'AgentListItem',
	props: ['agent'],
	components: {
		Input,
		FeatherIcon,
	},
    computed: {
        agentRoles() {
            if (this.agent) {
                return this.agent.roles ? this.agent.roles.join(', ') : ''
            }
            return ''
        }
    }
}
</script>

<style>

</style>