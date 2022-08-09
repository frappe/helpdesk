<template>
	<div class="pt-[17px] pl-[18px] pr-[24px]">
		<div class="flex flex-row space-x-[24px] h-full">
			<ArticleTitleAndContent :isNew="isNew" :editable="editMode" class="grow" :title="article.title" :content="article.content" :articleResource="$resources.article" @exit_edit_mode="() => { editMode = false }" />
			<ArticleDetails v-if="article" :isNew="isNew" class="w-[220px] shrink-0" :article="article" :articleResource="$resources.article" />
		</div>
	</div>
</template>

<script>
import ArticleTitleAndContent from '@/components/desk/knowledge_base/ArticleTitleAndContent.vue'
import ArticleDetails from '@/components/desk/knowledge_base/ArticleDetails.vue'
import { ref, provide } from 'vue'

export default {
	name: 'Article',
	props: ['articleId'],
	components: {
		ArticleTitleAndContent,
		ArticleDetails
	},
	mounted() {
		if (!this.articleId) {
			// toggle nav bar actions for new article
			const actions = [
				{ label: 'Cancel', appearance:'danger', handler: () => {
					this.$router.push('/frappedesk/knowledge-base/')
				}},
				{ label: 'Save', appearance: 'primary', handler: () => { this.saveNewArticle() }, dropdown: [
					{ label: 'Publish', appearance: 'secondary', handler: () => { this.saveNewArticle(true) } }
				] },
			]
			this.$event.emit('toggle_navbar_actions', ({type: "New Article", actions}))
		}

		this.saveNewArticle = (publish=false) => {
			this.insertArticle(publish)
		}
	},
	setup() {
		const editMode = ref(false)
		provide('editMode', editMode)
		
		const newArticleTempValues = ref({})
		const updateNewArticleInput = ref((input) => {
			newArticleTempValues.value[input.field] = input.value
		})
		provide('updateNewArticleInput', updateNewArticleInput)
		provide('newArticleTempValues', newArticleTempValues)

		const saveNewArticle = ref(() => {})
		provide('saveNewArticle', saveNewArticle)

		const saveArticleTitleAndContent = ref(() => {})
		provide('saveArticleTitleAndContent', saveArticleTitleAndContent)

		return {
			editMode,
			newArticleTempValues,
			saveNewArticle,
			saveArticleTitleAndContent,
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
					const actions = [
						{ label: 'Edit', appearance:'secondary', handler: () => {
							this.editMode = true
						}},
						{ label: doc.published ? 'Unpublish' : 'Publish', appearance: doc.published ? 'secondary' : 'primary', handler: () => {
							this.editMode = false
							this.$resources.article.setValue.submit({published: !doc.published})
						}}
					]
					this.$event.emit('toggle_navbar_actions', ({type: doc.published ? 'Published Article' : 'Draft Article', actions}))
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
						onError: (err) => {
							this.$toast({
								title: 'Error while updating article',
								text: err,
								customIcon: 'circle-fail',
								appearance: 'danger',
							})
						}
					}
				}
			} else {
				return {}
			}
		},
		newArticle() {
			return {
				method: 'frappe.client.insert',
				onSuccess: (doc) => {
					this.$router.push({path: '/frappedesk/knowledge-base/'})
				},
				onError: (err) => {
					this.$toast({
						title: 'Error while creating article',
						text: err,
						customIcon: 'circle-fail',
						appearance: 'danger',
					})
				}
			 }
		}
	},
	watch: {
		editMode(val) {
			if (val) {
				const actions = [
					{ label: 'Cancel', appearance:'danger', handler: () => {
						this.$router.go()
					}},
					{ label: 'Save', appearance: 'primary', handler: () => { this.saveArticleTitleAndContent() }, dropdown: [
						{ label: 'Publish', appearance: 'secondary', handler: () => { this.saveArticleTitleAndContent(true) } }
					] },
				]
				this.$event.emit('toggle_navbar_actions', ({type: "Edit Article", actions}))
			}
		}
	},
	methods: {
		insertArticle(publish=false) {
			const validateInputs = (input) => {
				if (!input.title || input.title == "") {
					return false
				}
				if (!input.content || input.content.replaceAll(' ', '') == '<p></p>') {
					return false
				}
				if (!input.author) {
					return false
				}
				if (!input.category) {
					return false
				}

				return true
			}

			if (validateInputs(this.newArticleTempValues)) {
				this.$resources.newArticle.submit({
					doc: {
						doctype: 'Article',
						title: this.newArticleTempValues.title,
						content: this.newArticleTempValues.content,
						author: this.newArticleTempValues.author,
						category: this.newArticleTempValues.category,
						note: this.insertArticle.note,
						published: publish
					}
				})
			}
		},
	}
}
</script>