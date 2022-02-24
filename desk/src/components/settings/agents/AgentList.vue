<template>
	<div>
		<div>
			<div
				v-if="agents"
				class="w-full block overflow-auto"
				:style="{ height: viewportWidth > 768 ? 'calc(100vh - 7.3rem)' : null }"
			>
				<div class="flex-auto" v-for="agent in agents" :key="agent.name">
					<div class="block px-0">
						<AgentListItem :agent="agent" />
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { Input } from 'frappe-ui'
import AgentListItem from './AgentListItem.vue'

export default {
	name: 'AgentList',
	inject: ['viewportWidth'],
	props: ['agents'],
	components: {
		Input,
		AgentListItem
	},
	computed: {
	}
}
</script>
