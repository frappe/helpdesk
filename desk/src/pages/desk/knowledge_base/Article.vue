<template>
	<div class="pt-[17px] pl-[18px] pr-[24px]">
		<div class="flex flex-row space-x-[24px]">
			<ArticleTitleAndContent class="grow" :title="article.title" :content="article.content" />
			<ArticleDetails v-if="article" class="w-[220px] shrink-0" :article="article" :articleResource="$resources.article" />
		</div>
	</div>
</template>

<script>
import ArticleTitleAndContent from '../../../components/desk/knowledge_base/ArticleTitleAndContent.vue'
import ArticleDetails from '../../../components/desk/knowledge_base/ArticleDetails.vue'

export default {
	name: 'Article',
	props: ['articleId'],
	components: {
		ArticleTitleAndContent,
		ArticleDetails
	},
	computed: {
		isNew() {
			return this.articleId ? false : true
		},
		article() {
			if (!this.isNew) {
				const doc = this.$resources.article.doc
				
				if (doc) {
					this.$event.emit('toggle_navbar_actions', doc.published ? 'Published Article' : 'Draft Article')
				}

				return doc || {}
			} 
			
			return {}
		}
	},
	resources: {
		article() {
			if (!this.isNew) {
				return {
					type: 'document',
					doctype: 'Article',
					name: this.articleId,
					setValue: {
						onSuccess: (doc) => {
							this.$toast({
								title: 'Article updated',
								customIcon: 'circle-check',
								appearance: 'success'
							})
						},
						onError: () => {
							this.$toast({
								title: 'Error while updating article',
								customIcon: 'circle-fail',
								appearance: 'danger',
							})
						}
					}
				}
			} else {
				return false
			}
		}
	}
}
</script>