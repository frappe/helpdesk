<template>
	<div class="flex flex-col" v-if="article">
		<div class="shrink-0 h-[72px] py-[22px] flow-root px-[16px]">
			<div class="float-left">
				<router-link
					:to="`/frappedesk/kb/${
						article.category || $route.query.category
					}`"
					class="my-1 text-[12px] text-gray-600 stroke-gray-600 flex flex-row items-center space-x-1 hover:text-gray-700 hover:stroke-gray-700 select-none"
					role="button"
				>
					<FeatherIcon name="arrow-left" class="w-[13px] h-[13px]" />
					<div>
						Back to {{ article.category || $route.query.category }}
					</div>
				</router-link>
			</div>
			<div class="float-right">
				<div v-if="!editMode" class="flex flex-row space-x-2">
					<Button
						appearance="secondary"
						@click="
							() => {
								editMode = true
								newArticleTempValues = {
									title: article.title,
									content: article.content,
									published: article.published,
									author: article.author,
									category: article.category,
									note: article.note,
								}
							}
						"
					>
						Edit
					</Button>
					<Button
						v-if="article.published"
						appearance="secondary"
						@click="
							$resources.article.setValue.submit({
								published: false,
							})
						"
						>Unpublish</Button
					>
					<Button
						v-else
						appearance="primary"
						@click="
							$resources.article.setValue.submit({
								published: true,
							})
						"
						>Publish</Button
					>
				</div>
				<div v-else class="flex flex-row space-x-2">
					<Button
						appearance="secondary"
						@click="
							() => {
								if (isNew) {
									$router.push(
										`/frappedesk/kb/${article.category}`
									)
								} else {
									this.$router.go()
								}
							}
						"
						>Cancel</Button
					>
					<Button appearance="primary" @click="saveArticle()"
						>Save</Button
					>
				</div>
			</div>
		</div>
		<div
			class="flex flex-row space-x-[24px] h-full border-t px-[16px] py-[22px]"
		>
			<ArticleTitleAndContent
				:isNew="isNew"
				:editable="editMode"
				class="grow"
				:title="article.title"
				:content="article.content"
				:articleResource="$resources.article"
				@exit_edit_mode="
					() => {
						editMode = false
					}
				"
			/>
			<ArticleDetails
				v-if="article"
				:isNew="isNew"
				class="w-[220px] shrink-0"
				:article="article"
				:articleResource="$resources.article"
			/>
		</div>
	</div>
</template>

<script>
import ArticleTitleAndContent from "@/components/desk/knowledge_base/ArticleTitleAndContent.vue"
import ArticleDetails from "@/components/desk/knowledge_base/ArticleDetails.vue"
import { ref, provide } from "vue"
import { FeatherIcon } from "frappe-ui"

export default {
	name: "Article",
	props: ["articleId"],
	components: {
		ArticleTitleAndContent,
		ArticleDetails,
		FeatherIcon,
	},
	mounted() {
		if (!this.articleId) {
			this.editMode = true
		}
	},
	setup(props) {
		const editMode = ref(!props.articleId)
		provide("editMode", editMode)

		const newArticleTempValues = ref({})
		const updateNewArticleInput = ref((input) => {
			newArticleTempValues.value[input.field] = input.value
		})
		const articleInputErrors = ref({})
		provide("updateNewArticleInput", updateNewArticleInput)
		provide("newArticleTempValues", newArticleTempValues)
		provide("articleInputErrors", articleInputErrors)

		const saveArticleTitleAndContent = ref(() => {})
		provide("saveArticleTitleAndContent", saveArticleTitleAndContent)

		return {
			editMode,
			newArticleTempValues,
			saveArticleTitleAndContent,
			articleInputErrors,
		}
	},
	computed: {
		isNew() {
			return this.articleId ? false : true
		},
		article() {
			if (!this.isNew) {
				return this.$resources.article.doc || {}
			}
			return {}
		},
	},
	resources: {
		article() {
			if (!this.isNew) {
				return {
					type: "document",
					doctype: "Article",
					name: this.articleId,
					setValue: {
						onSuccess: () => {
							this.$toast({
								title: "Article updated",
								customIcon: "circle-check",
								appearance: "success",
							})
						},
						onError: (err) => {
							this.$toast({
								title: "Error while updating article",
								text: err,
								customIcon: "circle-fail",
								appearance: "danger",
							})
						},
					},
				}
			} else {
				return {}
			}
		},
		newArticle() {
			return {
				method: "frappe.client.insert",
				onSuccess: (doc) => {
					this.$router.push(`/frappedesk/kb/articles/${doc.name}`)
				},
				onError: (err) => {
					this.$toast({
						title: "Error while creating article",
						text: err,
						customIcon: "circle-fail",
						appearance: "danger",
					})
				},
			}
		},
	},
	methods: {
		saveArticle(publish = false) {
			if (this.validateArticleInputValues(this.newArticleTempValues)) {
				const inputParams = {
					title: this.newArticleTempValues.title,
					content: this.newArticleTempValues.content,
					author: this.newArticleTempValues.author,
					category: this.newArticleTempValues.category,
					note: this.newArticleTempValues.note,
					published: publish,
				}
				if (this.isNew) {
					this.$resources.newArticle.submit({
						doc: {
							doctype: "Article",
							...inputParams,
						},
					})
				} else {
					this.$resources.article.setValue.submit({
						...inputParams,
					})
					this.editMode = false
				}
			}
		},
		validateArticleInputValues(input) {
			this.articleInputErrors = {}
			if (!input.title || input.title == "") {
				this.articleInputErrors.title = "Title is required"
			}
			if (
				!input.content ||
				input.content.replaceAll(" ", "") == "<p></p>"
			) {
				this.articleInputErrors.content = "Content is required"
			}
			if (!input.author) {
				this.articleInputErrors.author = "Author is required"
			}
			if (!input.category) {
				this.articleInputErrors.category = "Category is required"
			}

			return Object.keys(this.articleInputErrors).length == 0
		},
	},
}
</script>
