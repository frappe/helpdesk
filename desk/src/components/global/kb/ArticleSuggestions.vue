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
import { debounce } from "frappe-ui"

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
	watch: {
		query(newVal) {
			if (this.$refs.suggestedArticles?.manager) {
				this.filterOutArticles(newVal)
			}
		},
	},
	methods: {
		filterOutArticles: debounce(function (query = "") {
			// TODO: filter should be applied to content too, but it's not indexed
			this.$refs.suggestedArticles.manager.addFilters([
				{
					fieldname: "title",
					filter_type: "like",
					value: query,
				},
				{
					fieldname: "status",
					filter_type: "is",
					value: "Published",
				},
			])
			this.$refs.suggestedArticles.manager.reload()
		}, 500),
	},
}
</script>
