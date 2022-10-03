<template>
	<div class="text-base rounded-md h-[30px] w-[120px] bg-gray-100 p-[3px] select-none">
		<div v-if="viewMode === 'Web'" class="flex flex-row items-center space-x-2">
			<FeatherIcon
				role="button"
				@click="() => { viewMode = 'List' }"
				name="list" 
				class="h-5 w-5 ml-2 stroke-gray-500 hover:stroke-gray-900"
			/>
			<div 
				class="bg-white rounded-md shadow px-2 py-0.5 w-[82px] h-[24px]"
			>
				Webview
			</div>
		</div>
		<div v-else class="flex flex-row items-center space-x-2">
			<div 
				class="bg-white rounded-md shadow px-2 py-0.5 w-[82px] h-[24px]"
			>
				{{ selectedList }}
			</div>
			<FeatherIcon
				role="button"
				@click="() => { viewMode = 'Web' }"
				name="layout"
				class="h-5 w-5 mr-2 stroke-gray-500 hover:stroke-gray-900"
			/>
		</div>
	</div>
</template>

<script>
import { FeatherIcon } from 'frappe-ui';

export default {
	name: 'KBLayoutSwitcher',
	props: {
		viewMode: {
			type: String,
			default: 'Web'
		},
		selectedList: {
			type: String,
			default: 'Articles' // Articles, Categories
		}
	},
	components: {
		FeatherIcon
	},
}
</script>