<template>
	<div
		class="flex flex-row space-x-2 items-center group"
		:class="editMode ? 'cursor-grab' : 'cursor-pointer'"
	>
		<CustomIcons v-if="editMode" name="list-drag-handle" class="w-4 h-4" />
		<FeatherIcon
			v-else
			name="file-text"
			class="h-4 w-4 stroke-gray-500 group-hover:stroke-gray-600"
		/>
		<div
			class="text-base text-gray-700"
			:class="editMode ? '' : 'group-hover:text-gray-900'"
		>
			{{ article.title }}
		</div>
	</div>
</template>

<script>
import { FeatherIcon } from "frappe-ui"
import CustomIcons from "@/components/desk/global/CustomIcons.vue"

export default {
	name: "ArticleMiniListItem",
	props: {
		article: {
			type: Object,
			default: null,
		},
		editMode: {
			type: Boolean,
			default: false,
		},
	},
	components: {
		FeatherIcon,
		CustomIcons,
	},
}
</script>
