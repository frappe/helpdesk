<template>
	<div class="text-base rounded-md h-[30px] bg-gray-100 p-[3px] select-none">
		<div
			v-if="viewMode === 'Web'"
			class="flex flex-row items-center space-x-2"
		>
			<RouterLink
				:title="'Articles'"
				:to="{
					path: '/kb/articles',
				}"
			>
				<FeatherIcon
					role="button"
					name="list"
					class="h-5 w-5 ml-2 stroke-gray-500 hover:stroke-gray-900"
				/>
			</RouterLink>
			<div
				class="bg-white rounded-md shadow px-2 py-0.5 w-[82px] h-[24px]"
			>
				Webview
			</div>
		</div>
		<div v-else class="flex flex-row items-center space-x-2">
			<div
				class="bg-white rounded-md shadow px-2 py-0.5 w-[82px] h-[24px] group"
			>
				<div>Articles</div>
			</div>
			<RouterLink
				:title="'Toggle Web view'"
				:to="{ path: '/kb' }"
			>
				<FeatherIcon
					role="button"
					name="layout"
					class="h-5 w-5 mr-2 stroke-gray-500 hover:stroke-gray-900"
				/>
			</RouterLink>
		</div>
	</div>
</template>

<script>
import { FeatherIcon } from "frappe-ui"

export default {
	name: "LayoutSwitcher",
	props: {
		viewMode: {
			type: String,
			default: "Web",
		},
	},
	components: {
		FeatherIcon,
	},
}
</script>
