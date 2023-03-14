<template>
	<EditableBlock
		class="h-full"
		:editable="editable"
		:editMode="editMode"
		:saveInProgress="saveInProgress"
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
				} else {
					$toast({
						title: 'Validation Error',
						text: 'Please fix the errors before saving',
						icon: 'x',
						iconClasses: 'text-red-500',
					})
				}
			}
		"
	>
		<template #body>
			<div
				:class="
					editable
						? `rounded-md p-5 h-full overflow-y-auto ${
								editMode ? 'border-2 border-gray-300' : 'shadow'
						  }`
						: ''
				"
			>
				<div class="grid grid-cols-1 place-content-center">
					<SearchSection
						:disabled="editable"
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
								:isDesk="editable"
								class="mb-5"
							/>
						</div>
						<CategoryCardList
							as="div"
							ref="categoryCardList"
							:categoryId="categoryId"
						/>
						<ArticleMiniList
							as="div"
							v-if="!isRoot"
							ref="articleMiniList"
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
import { ref, provide } from "vue"
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
	data() {
		return {
			isMounted: false,
		}
	},
	setup() {
		const route = useRoute()
		const editable = ref(route.meta.editable)

		const isRoot = ref(route.meta.isRoot)
		provide("isRoot", isRoot)

		const editMode = ref(false)
		provide("editMode", editMode)

		const saveInProgress = ref(false)

		return {
			editable,
			editMode,

			isRoot,

			saveInProgress,
		}
	},
	computed: {
		isEmpty() {
			if (!this.isMounted) return
			var articles = 0
			var categories = 0
			if (!this.isRoot) {
				if (this.$refs.articleMiniList.list.loading) {
					return
				}
				articles = this.$refs.articleMiniList.list.data.length
			}
			if (!this.$refs.categoryCardList.list.loading) {
				categories = this.$refs.categoryCardList.list.data.length
			} else {
				return
			}
			const isEmpty = articles + categories === 0
			if (this.editable) {
				this.editMode = isEmpty
			}
			return isEmpty
		},
	},
	mounted() {
		this.isMounted = true
	},
	methods: {
		validateChanges() {
			return (
				this.$refs.categoryCardList.validateChanges() &&
				(this.$refs.articleMiniList
					? this.$refs.articleMiniList.validateChanges()
					: true)
			)
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
}
</script>
