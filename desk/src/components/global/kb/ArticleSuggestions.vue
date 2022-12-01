<template>
	<div class="flex flex-col space-y-2 w-full">
		<div class="text-[16px] font-medium">Related Articles</div>
		<ListManager
			ref="suggestedArticles"
			:options="{
				doctype: 'Article',
				fields: [
					'title',
					'content',
					'category',
					'author',
					'creation',
					'modified',
				],
				limit: 5,
				order_by: 'modified desc',
				filters: [['Article', 'status', '=', 'Published']],
			}"
		>
			<template #body="{ manager }">
				<div class="flex flex-col space-y-2">
					<div v-for="item in manager.list" :key="item.name">
						<ArticleCard :article="item" class="w-full" />
					</div>
				</div>
			</template>
		</ListManager>
	</div>
</template>

<script>
import ListManager from "@/components/global/ListManager.vue"
import ArticleCard from "./ArticleCard.vue"

export default {
	name: "ArticleSuggestions",
	props: {
		query: {
			type: String,
			default: "",
		},
	},
	components: {
		ListManager,
		ArticleCard,
	},
}
</script>
