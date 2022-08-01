<template>
	<div class="text-[13px] font-normal p-5">
		<ListManager
			ref="articleList"
			:options="{
				doctype: 'Article',
				fields: [
					'title',
					'author',
					'views',
					'modified'
				],
				filters: [['category', '=', subCategory]],
				order_by: 'modified desc',
				limit: 20
			}"
		>
			<template #body="{ manager }">
				<div>
					<ArticleList :manager="manager" />
				</div>
			</template>
		</ListManager>
	</div>
</template>

<script>
import ListManager from '@/components/global/ListManager.vue'
import ArticleList from '@/components/desk/knowledge_base/ArticleList.vue'

export default {
	name: 'KnowledgeBaseCategory',
	props: {
		category: {
			type: String,
			default: '',
		},
		subCategory: {
			type: String,
			default: '',
		},
	},
	components: {
		ListManager,
		ArticleList
	},
}
</script>