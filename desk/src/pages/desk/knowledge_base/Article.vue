<template>
	<div class="pt-[17px] pl-[18px] pr-[24px]">
		<div class="flex flex-row space-x-[24px] h-full">
			<ArticleTitleAndContent :editable="editMode" class="grow" :title="article.title" :content="article.content" :articleResource="$resources.article" @exit_edit_mode="() => { editMode = false }" />
			<ArticleDetails v-if="article" class="w-[220px] shrink-0" :article="article" :articleResource="$resources.article" />
		</div>
	</div>
</template>

<script>
import ArticleTitleAndContent from '../../../components/desk/knowledge_base/ArticleTitleAndContent.vue'
import ArticleDetails from '../../../components/desk/knowledge_base/ArticleDetails.vue'
import { ref } from '@vue/reactivity'

export default {
	name: 'Article',
	props: ['articleId'],
	components: {
		ArticleTitleAndContent,
		ArticleDetails
	},
	mounted() {
		this.$event.on('edit_current_article', () => {
			this.editMode = true
			this.$event.emit('toggle_navbar_actions', 'Edit Article')
		})
		this.$event.on('publish_current_article', () => {
			this.$resources.article.setValue.submit({published:  true})
		})
		this.$event.on('unpublish_current_article', () => {
			this.$resources.article.setValue.submit({published:  false})
		})
	},
	unmounted() {
		this.$event.off('edit_current_article')
		this.$event.off('publish_current_article')
		this.$event.off('unpublish_current_article')
	},
	setup() {
		const editMode = ref(false)

		return {
			editMode
		}
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
						onSuccess: () => {
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