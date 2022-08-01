<template>
	<div class="w-full flex flex-row items-center px-[24px]">
		<div class="grow">
			<span class="font-semibold tex-[16px] text-gray-900">Knowledge Base</span>
		</div>
		<div>
			<div class="flex flex-row items-center space-x-2 bg-blue-500 rounded-[6px] px-[10px]" role="button">
				<div 
					class="border-r border-blue-400 pr-2 text-white text-base font-normal py-[4px]" 
					@click="$router.push({path: '/frappedesk/knowledge-base/new-article'})"
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
		</div>
	</div>
</template>

<script>
import { Dropdown, FeatherIcon } from 'frappe-ui'

export default {
	name: 'TopNavbar',
	components: {
		Dropdown,
		FeatherIcon
	},
}
</script>

<style>

</style>