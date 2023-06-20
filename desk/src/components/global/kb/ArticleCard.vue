<template>
	<RouterLink :to="`/knowledge-base/articles/${article.name}`">
		<div
			class="group rounded-[6px] shadow-md bg-white p-5 w-full flex flex-row justify-between items-center hover:bg-gray-50"
		>
			<div class="text-base text-gray-600">
				{{ article.title }}
			</div>
			<FeatherIcon
				name="chevron-right"
				class="h-4 w-4 group-hover:visible invisible"
			/>
		</div>
	</RouterLink>
</template>

<script>
import { TextEditor, FeatherIcon } from "frappe-ui"

export default {
	name: "ArticleCard",
	props: {
		article: {
			type: Object,
		},
	},
	components: {
		TextEditor,
		FeatherIcon,
	},
}
</script>
