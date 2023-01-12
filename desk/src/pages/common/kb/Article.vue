<template>
	<EditableBlock
		class="h-full"
		:editable="editable"
		:editMode="editMode"
		:saveInProgress="saveInProgress"
		:disableSaving="disableSaving"
		@edit="
			() => {
				editMode = true
				articleTempValues = { ...article } || {}
			}
		"
		@discard="
			() => {
				if (isNew) {
					$router.push({ path: '/helpdesk/kb/articles' })
				} else {
					editMode = false
				}
			}
		"
		@save="saveChanges"
	>
		<template #top-left-section>
			<div>
				<Breadcrumbs
					v-if="!isNew"
					docType="Article"
					:docName="articleId"
					:isDesk="editable"
				/>
				<BaseBreadcrumbs
					v-else
					:breadcrumbs="[
						{
							label: 'Articles',
							name: 'articles',
							handler: () => {
								$router.push({
									path: `/${
										editable ? 'helpdesk' : 'support'
									}/kb/articles`,
								})
							},
						},
						{
							label: 'New',
							name: 'new',
						},
					]"
				/>
			</div>
		</template>
		<template #other-main-actions>
			<div>
				<Button
					:loading="saveInProgress"
					:appearance="
						article.status === 'Published' ? 'secondary' : 'primary'
					"
					@click="
						() => {
							articleTempValues = { ...article }
							saveChanges(!(article.status === 'Published'))
						}
					"
				>
					{{
						article.status === "Published" ? "Unpublish" : "Publish"
					}}
				</Button>
			</div>
		</template>
		<template #save-action="{ save, disableSaving, saveInProgress }">
			<Dropdown
				placement="right"
				:options="[
					{
						label: 'Save',
						handler: () => {
							save()
						},
					},
					{
						label: 'Save and Publish',
						handler: () => {
							save(true)
						},
					},
				]"
			>
				<template v-slot="{ toggleDropdown }">
					<Button
						:loading="saveInProgress"
						icon-right="chevron-down"
						class="ml-2"
						:class="disableSaving ? 'cursor-not-allowed' : ''"
						:disable="disableSaving"
						@click="toggleDropdown"
					>
						Save
					</Button>
				</template>
			</Dropdown>
		</template>
		<template #body>
			<div class="h-full grid grid-cols-1">
				<SearchSection
					v-if="!editable"
					:disabled="editable"
					class="mb-5"
				/>
				<div
					class="flex flex-col h-full"
					:class="editable ? '' : 'container mx-auto'"
				>
					<Breadcrumbs
						v-if="!editable"
						docType="Article"
						:docName="articleId"
						:isDesk="editable"
						class="mb-5"
					/>
					<div class="flex flex-row space-x-[24px] grow">
						<ArticleTitleAndContent
							class="grow"
							:editable="editable"
							:editMode="editMode"
							:article="article"
						/>
						<div class="w-[250px] shrink-0">
							<ArticleDetails
								v-if="editable"
								:article="article"
								:articleResource="$resources.article"
								:isNew="isNew"
							/>
							<!-- TODO: <RelatedArticles v-else :articleId="articleId" /> -->
						</div>
					</div>
					<ArticleFeedback v-if="!editable" :article="article" />
				</div>
			</div>
		</template>
	</EditableBlock>
</template>

<script>
import EditableBlock from "@/components/global/kb/EditableBlock.vue"
import SearchSection from "@/components/global/kb/SearchSection.vue"
import Breadcrumbs from "@/components/global/kb/Breadcrumbs.vue"
import ArticleDetails from "@/components/desk/kb/ArticleDetails.vue"
import ArticleTitleAndContent from "@/components/desk/kb/ArticleTitleAndContent.vue"
import { useRoute } from "vue-router"
import { ref, provide, inject } from "vue"
import { Dropdown, FeatherIcon } from "frappe-ui"
import BaseBreadcrumbs from "@/components/global/BaseBreadcrumbs.vue"
import ArticleFeedback from "@/components/portal/kb/ArticleFeedback.vue"

export default {
	name: "Article",
	props: {
		articleId: {
			type: String,
			default: null,
		},
	},
	components: {
		EditableBlock,
		SearchSection,
		Breadcrumbs,
		ArticleDetails,
		ArticleTitleAndContent,
		Dropdown,
		FeatherIcon,
		BaseBreadcrumbs,
		ArticleFeedback,
	},
	setup() {
		const user = inject("user")
		const route = useRoute()
		const editable = ref(route.meta.editable)
		const isNew = ref(route.meta.isNew || false)

		const editMode = ref(route.meta.editMode || false)
		const saveInProgress = ref(false)

		const articleTempValues = ref({})
		if (isNew) {
			articleTempValues.value = {
				author: user.value.user,
				category: route.meta.category || null,
			}
		}
		const updateArticleTempValues = ref(() => {})
		const articleInputErrors = ref({})
		const validators = ref({})
		provide("updateArticleTempValues", updateArticleTempValues)
		provide("articleTempValues", articleTempValues)
		provide("articleInputErrors", articleInputErrors)

		return {
			editable,
			isNew,
			editMode,
			saveInProgress,
			articleTempValues,
			updateArticleTempValues,
			articleInputErrors,
			validators,
		}
	},
	mounted() {
		this.validators = {
			title: this.validateTitle,
			content: this.validateContent,
			author: this.validateAuthor,
			category: this.validateCategory,
		}

		this.updateArticleTempValues = (input) => {
			this.articleTempValues[input.field] = input.value
			this.validators[input.field](input.value)
		}

		if (!this.editable) {
			this.$resources.incrementArtileViews.submit({
				article: this.articleId,
			})
		}
	},
	computed: {
		disableSaving() {
			return false
		},
		article() {
			if (!this.isNew) {
				return this.editable
					? this.$resources.article.doc || {}
					: this.$resources.article.data || {}
			}
			return {}
		},
	},
	resources: {
		incrementArtileViews: {
			method: "helpdesk.api.kb.increment_article_views",
		},
		article() {
			if (!this.isNew) {
				if (this.editable) {
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
					return {
						method: "helpdesk.api.kb.get_article",
						params: {
							article: this.articleId,
						},
						auto: true,
					}
				}
			} else {
				return {}
			}
		},
		newArticle() {
			return {
				method: "frappe.client.insert",
				onSuccess: (doc) => {
					this.$router.push(`/helpdesk/kb/articles/${doc.name}`)
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
		checkIfTitleExists() {
			return {
				method: "helpdesk.api.kb.check_if_article_title_exists",
				onSuccess: (exists) => {
					if (exists) {
						this.articleInputErrors.title =
							"Article with this title already exists"
					} else {
						this.articleInputErrors.title = ""
					}
				},
			}
		},
	},
	methods: {
		async validateTitle(value) {
			this.articleInputErrors.titlle = ""
			if (!value || value == "") {
				this.articleInputErrors.title = "Title is required"
			} else if (value.length <= 3) {
				this.articleInputErrors.title =
					"Title should be atleast 3 characters long"
			} else {
				await this.$resources.checkIfTitleExists.submit({
					title: value,
					name: this.isNew ? null : this.article.name,
				})
			}
			return this.articleInputErrors.title
		},
		validateContent(value) {
			this.articleInputErrors.content = ""
			if (!value || value.replaceAll(" ", "") == "<p></p>") {
				this.articleInputErrors.content = "Content is required"
			}
			return this.articleInputErrors.content
		},
		validateAuthor(value) {
			this.articleInputErrors.author = ""
			if (!value) {
				this.articleInputErrors.author = "Author is required"
			}
			return this.articleInputErrors.author
		},
		validateCategory(value) {
			this.articleInputErrors.category = ""
			if (!value) {
				this.articleInputErrors.category = "Category is required"
			}
			return this.articleInputErrors.category
		},
		async validateChanges() {
			const input = this.articleTempValues

			let errors = ""
			errors += await this.validateTitle(input.title)
			errors += this.validateContent(input.content)
			errors += this.validateAuthor(input.author)
			errors += this.validateCategory(input.category)

			return errors.length == 0
		},
		async saveChanges(publish = false) {
			if (await this.validateChanges()) {
				this.saveInProgress = true
				if (this.isNew) {
					this.articleTempValues.status = publish
						? "Published"
						: "Draft"
					await this.$resources.newArticle.submit({
						doc: {
							doctype: "Article",
							...this.articleTempValues,
						},
					})
				} else {
					// page is reloaded to fetch the new breadcrumbs
					// TODO: find a better way to do this
					let reloadPage =
						this.articleTempValues.title != this.article.title
					await this.$resources.article.setValue.submit({
						title: this.articleTempValues.title,
						content: this.articleTempValues.content,
						status: publish ? "Published" : "Draft",
					})
					if (reloadPage) {
						this.$router.go()
					}
				}
				this.editMode = false
				this.saveInProgress = false
			}
			return
		},
	},
}
</script>
