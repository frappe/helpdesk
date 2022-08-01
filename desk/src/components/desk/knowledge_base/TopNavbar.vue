<template>
	<div class="w-full flex flex-row items-center px-[24px]">
		<div class="grow">
			<span class="font-semibold tex-[16px] text-gray-900">Knowledge Base</span>
		</div>
		<div>
			<div v-if="actionType == 'Category'" class="flex flex-row items-center space-x-2 bg-blue-500 rounded-[6px] px-[10px]" role="button">
				<div 
					class="border-r border-blue-400 pr-2 text-white text-base font-normal py-[6px]" 
					@click="$router.push({name: 'NewArticle', path: '/frappedesk/knowledge-base/articles/new'})"
				>
					Add article
				</div>
				<Dropdown :options="[{ label: 'Add category', handler: () => { $event.emit('create_new_category') }}]">
					<template v-slot="{ toggle }">
						<div class="py-[4px]" @click="toggle">
							<FeatherIcon name="chevron-down" class="w-4 h-4 stroke-blue-400" role="button" />
						</div>
					</template>
				</Dropdown>
			</div>
			<div v-else-if="actionType == 'Article'" class="flex flex-row space-x-[12px]">
				<Button appearane="secondary">Save</Button>
				<Button appearance="primary">Publish</Button>
			</div>
		</div>
	</div>
</template>

<script>
import { Dropdown, FeatherIcon } from 'frappe-ui'
import { ref } from '@vue/reactivity'

export default {
	name: 'TopNavbar',
	components: {
		Dropdown,
		FeatherIcon
	},
	setup() {
		const actionType = ref('Category')

		return {
			actionType
		}
	},
	mounted() {
		this.$event.on('toggle_navbar_actions', (type="Category") => {
			this.actionType = type
		})
	},
	unmounted() {
		this.$event.off('toggle_navbar_actions')
	}
}
</script>