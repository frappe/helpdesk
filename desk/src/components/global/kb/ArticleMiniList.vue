<template>
	<!-- TODO: option to add articles via combobox, create new articles too ? -->
	<div
		v-if="categoryId && (articles?.length > 0 || editMode)"
		class="flex flex-col space-y-5"
	>
		<div class="flex flex-row space-x-2 items-center">
			<div class="text-3xl font-bold text-gray-800">Articles</div>
			<!-- TODO: <FeatherIcon v-if="editMode" name="plus" class="w-4 cursor-pointer my-auto bg-gray-50 hover:bg-gray-100 rounded" /> -->
			<p v-if="editMode" class="text-base text-gray-500">
				( add articles from
				<router-link
					class="underline"
					:to="{ path: '/frappedesk/kb/articles' }"
					>here</router-link
				>
				)
			</p>
		</div>
		<draggable
			:list="articles"
			:disabled="!editMode"
			item-key="idx"
			class="grow grid place-content-center gap-y-3"
			:class="articles?.length > 6 ? 'grid-cols-2' : 'grid-cols-1'"
		>
			<template #item="{ element }">
				<div class="flex flex-row items-center space-x-1">
					<ArticleMiniListItem
						:editMode="editMode"
						:article="element"
						@click="
							() => {
								if (editMode) return
								$router.push({
									path: `/${
										editable ? 'frappedesk' : 'support'
									}/kb/articles/${element.name}`,
								})
							}
						"
					/>
				</div>
			</template>
		</draggable>
	</div>
</template>

<script>
import { ref, provide, computed, inject } from "vue"
import draggable from "vuedraggable"
import ArticleMiniListItem from "@/components/global/kb/ArticleMiniListItem.vue"
import { FeatherIcon } from "frappe-ui"

export default {
	name: "ArticleMiniList",
	props: {
		categoryId: {
			type: String,
			default: null,
		},
	},
	components: {
		draggable,
		ArticleMiniListItem,
		FeatherIcon,
	},
	setup(props, context) {
		const tempArticles = ref([])
		const allValidationErrors = ref([])

		provide("allValidationErrors", allValidationErrors)

		const resources = ref(null)

		const saveInProgress = computed(() => {
			return resources.value.saveArticles.loading
		})
		const validateChanges = () => {
			return allValidationErrors.value.length == 0
		}
		const saveChanges = async () => {
			if (!props.categoryId) return
			await resources.value.saveArticles.submit({
				new_values: tempArticles.value,
			})
		}

		const editable = inject("editable")
		const editMode = inject("editMode")

		const list = ref({
			loading: true,
			data: [],
		})

		context.expose({
			list,
			saveInProgress,
			validateChanges,
			saveChanges,
		})

		return {
			list,
			tempArticles,
			allValidationErrors,
			resources,
			editMode,
			editable,
		}
	},
	mounted() {
		this.resources = this.$resources
	},
	computed: {
		articles() {
			if (!this.editMode) {
				this.list.loading = this.$resources.articles.loading
				this.list.data = this.$resources.articles.data || []
				return this.list.data
			} else {
				return this.tempArticles
			}
		},
	},
	expose: ["articles"],
	watch: {
		editMode(newVal) {
			if (newVal) {
				this.tempArticles = JSON.parse(
					JSON.stringify(this.$resources.articles.data)
				)
			}
		},
	},
	resources: {
		articles() {
			const filters = { category: this.categoryId, status: "Published" }
			const fields = ["name", "title", "idx"]

			if (this.editable) {
				return {
					cache: ["Articles", this.categoryId, "published"],
					type: "list",
					doctype: "Article",
					filters,
					fields: [...fields, "status"],
					limit: 999,
					order_by: "idx",
					// realtime: true TODO: if there are any updates inform the user via some promt (also handle editMode: true senarios)
					// or implement colaborative editing
				}
			} else {
				return {
					cache: ["Articles", this.categoryId, "published"],
					method: "frappedesk.api.kb.get_articles",
					params: {
						filters,
						fields,
						limit: 999,
						order_by: "idx",
					},
					auto: true,
				}
			}
		},
		saveArticles() {
			return {
				method: "frappedesk.api.kb.update_articles_order_and_status",
				onSuccess: () => {
					this.$resources.articles.reload()

					this.$toast({
						title: "Articles updated!!",
						customIcon: "circle-check",
						appearance: "success",
					})
				},
				onError: (err) => {
					this.$toast({
						title: "Error while saving",
						text: err,
						customIcon: "circle-fail",
						appearance: "danger",
					})
				},
			}
		},
	},
}
</script>
