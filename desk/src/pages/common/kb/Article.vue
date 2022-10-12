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
				editMode = false
			}
		"
		@save="
			(publish = false) => {
				if (validateChanges()) {
					saveChanges(publish).then(() => {
						// TODO: remove the $router.go() hack,
						// instead reload the breadcrumbs on top if
						// the name of the article is changed
						editMode = false
					})
				}
			}
		"
	>
		<template #top-left-section>
			<Breadcrumbs
				docType="Article"
				:docName="articleId"
				:isDesk="editable"
			/>
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
						icon-left="save"
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
				<SearchSection v-if="!editable" class="mb-5" />
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
					<div class="flex flex-row space-x-2 grow">
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
import { ref, provide } from "vue"
import { Dropdown } from "frappe-ui"

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
	},
	setup() {
		const route = useRoute()
		const editable = ref(route.meta.editable)
		const isNew = ref(route.meta.isNew)

		const editMode = ref(false)
		const saveInProgress = ref(false)

		const articleTempValues = ref({})
		const updateArticleTempValues = ref((input) => {
			articleTempValues.value[input.field] = input.value
		})
		const articleInputErrors = ref({})
		provide("updateArticleTempValues", updateArticleTempValues)
		provide("articleTempValues", articleTempValues)
		provide("articleInputErrors", articleInputErrors)

		return {
			editable,
			isNew,
			editMode,
			saveInProgress,
			articleTempValues,
			articleInputErrors,
		}
	},
	computed: {
		disableSaving() {
			return false
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
		validateChanges() {
			const input = this.articleTempValues
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
		async saveChanges(publish = false) {
			this.saveInProgress = true
			if (this.isNew) {
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
			this.saveInProgress = false
			return
		},
	},
}
</script>
