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
			}
		"
		@discard="
			() => {
				editMode = false
			}
		"
		@save="
			() => {
				if (validateChanges()) {
					saveChanges().then(() => {
						editMode = false
					})
				}
			}
		"
	>
		<template #body>
			<div
				:class="
					editable
						? `rounded-md p-5 h-full overflow-y-scroll ${
								editMode ? 'border-2 border-gray-300' : 'shadow'
						  }`
						: ''
				"
			>
				<div class="grid grid-cols-1 place-content-center">
					<SearchSection
						:isRoot="isRoot"
						:class="isRoot ? 'mb-14' : 'mb-5'"
					/>
					<div
						class="flex flex-col"
						:class="editable ? '' : 'container mx-auto'"
					>
						<div v-if="!isRoot">
							<Breadcrumbs
								docType="Category"
								:docName="categoryId"
								class="mb-5"
							/>
						</div>
						<CategoryCardList
							as="div"
							ref="categoryCardList"
							:editable="editable"
							:editMode="editMode"
							:categoryId="categoryId"
						/>
						<ArticleMiniList
							as="div"
							v-if="!isRoot"
							ref="articleMiniList"
							:editable="editable"
							:editMode="editMode"
							:categoryId="categoryId"
						/>
						<div
							v-if="isEmpty && !editMode"
							class="text-base text-gray-600"
						>
							Its empty here
						</div>
						<!-- <LinkCards :editable="editable">
							TODO: These cards can be used to add any links, eg: link to an article etc..
						</LinkCards> -->
						<!-- <FAQList :editable="editable">
							TODO: Show FAQ edit list
						</FAQList> -->
					</div>
				</div>
			</div>
		</template>
	</EditableBlock>
</template>

<script>
import { ref } from "vue"
import { useRoute } from "vue-router"
import CategoryCardList from "@/components/global/kb/CategoryCardList.vue"
import ArticleMiniList from "@/components/global/kb/ArticleMiniList.vue"
import EditableBlock from "@/components/global/kb/EditableBlock.vue"
import SearchSection from "@/components/global/kb/SearchSection.vue"
import Breadcrumbs from "@/components/global/kb/Breadcrumbs.vue"

export default {
	name: "Category",
	components: {
		CategoryCardList,
		ArticleMiniList,
		EditableBlock,
		SearchSection,
		Breadcrumbs,
	},
	props: {
		categoryId: {
			type: String,
			default: null,
		},
	},
	setup() {
		const route = useRoute()
		const editable = ref(route.meta.editable)

		const isRoot = ref(route.meta.isRoot)

		const editMode = ref(false)
		const saveInProgress = ref(false)

		return {
			editable,
			editMode,

			isRoot,

			saveInProgress,
		}
	},
	computed: {
		disableSaving() {
			// TODO: check of validation errors etc
			return false
			// return this.$refs.categoryCardList?.disableSaving // || this.$refs.articleMiniList?.disableSaving
		},
		isEmpty() {
			if (
				this.$resources.articlesCount.loading ||
				this.$resources.subCategoriesCount.loading
			)
				return
			const isEmpty =
				this.$resources.subCategoriesCount.data === 0 &&
				this.$resources.subCategoriesCount.data === 0
			if (this.editable) this.editMode = isEmpty
			return isEmpty
		},
	},
	methods: {
		validateChanges() {
			return this.$refs.categoryCardList.validateChanges() &&
				this.$refs.articleMiniList
				? this.$refs.articleMiniList.validateChanges()
				: true
		},
		async saveChanges() {
			this.saveInProgress = true
			await this.$refs.categoryCardList.saveChanges()
			if (this.$refs.articleMiniList)
				await this.$refs.articleMiniList.saveChanges()
			this.saveInProgress = false
			return
		},
	},
	resources: {
		articlesCount() {
			return {
				method: "frappe.client.get_count",
				params: {
					doctype: "Article",
					filters: {
						category: this.categoryId,
						status: "Published",
					},
				},
				auto: true,
			}
		},
		subCategoriesCount() {
			return {
				method: "frappe.client.get_count",
				params: {
					doctype: "Category",
					filters: {
						parent_category: this.categoryId,
						status: "Published",
					},
				},
				auto: true,
			}
		},
	},
}
</script>
