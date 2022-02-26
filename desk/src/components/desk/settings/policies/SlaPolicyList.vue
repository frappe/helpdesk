<template>
	<div>
		<div>
			<div
				v-if="policies"
				class="w-full block overflow-auto"
				:style="{ height: viewportWidth > 768 ? 'calc(100vh - 7.3rem)' : null }"
			>
				<div class="flex-auto" v-for="policy in policies" :key="policy.name">
					<div class="block px-0">
						<SlaPolicyListItem :policy="policy" />
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { Input } from 'frappe-ui'
import SlaPolicyListItem from './SlaPolicyListItem.vue'

export default {
	name: 'SlaPolicyList',
	inject: ['viewportWidth'],
	props: ['policies'],
	components: {
		Input,
		SlaPolicyListItem
	},
	computed: {
	}
}
</script>
