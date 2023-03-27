<template>
	<!-- TODO: if no category exists then show a sudo category card (dashed border or something) to fill the edit space -->
	<draggable
		v-if="(categories && categories.length > 0) || editMode"
		:list="categories"
		:disabled="!editMode"
		handle=".handle"
		item-key="idx"
		class="grid place-content-center grid-cols-3 gap-y-6 mb-5"
		:class="editMode ? 'gap-x-1 mr-[-1.25rem]' : 'gap-x-6'"
	>
		<template #item="{ element }">
			<div class="flex flex-row items-center space-x-1">
				<CategoryCard
					class="grow"
					:category="element"
					:deletable="isRoot ? categories.length > 1 : true"
					@delete="
						() => {
							allValidationErrors.splice(
								allValidationErrors.findIndex(
									(c) => c == element
								),
								1
							)
							categories.splice(
								categories.findIndex((c) => c == element),
								1
							)
						}
					"
					@click="
						() => {
							if (element.is_placeholder) {
								categories.splice(
									categories.indexOf(element),
									1
								) // remove placeholder card
								categories.push({
									is_new: true,
									idx: categories.length,
									category_name: '',
									description: '',
									parent_category: categoryId
										? categoryId
										: null,
									is_group: 1,
								})
								categories.push({
									is_placeholder: true,
								})
							}
							if (editMode) return
							return $router.push({
								path: `/${
									['DeskKBHome', 'DeskKBCategory'].includes(
										$route.name
									)
										? 'frappedesk'
										: 'support'
								}/kb/categories/${element.name}`,
							})
						}
					"
				/>
				<div v-if="editMode" class="group h-full">
					<div class="group-hover:visible invisible flex h-full">
						<FeatherIcon
							v-if="!element.is_placeholder"
							name="plus"
							class="w-4 cursor-pointer my-auto hover:bg-gray-100 rounded"
							@click="
								() => {
									const index = categories.findIndex(
										(c) => c == element
									)
									categories.splice(index + 1, 0, {
										is_new: true,
										idx: categories.length,
										category_name: '',
										description: '',
										parent_category: categoryId
											? categoryId
											: null,
										is_group: 1,
									})
								}
							"
						/>
					</div>
				</div>
			</div>
		</template>
	</draggable>
</template>

<script>
import { provide, ref, computed, inject } from "vue"
import draggable from "vuedraggable"
import { FeatherIcon } from "frappe-ui"
import CategoryCard from "@/components/global/kb/CategoryCard.vue"

export default {
	name: "CategoryCardList",
	props: {
		categoryId: {
			type: String,
			default: null,
		},
	},
	components: {
		draggable,
		CategoryCard,
		FeatherIcon,
	},
	setup(props, context) {
		const editMode = inject("editMode")
		const isRoot = inject("isRoot")
		const tempCategories = ref([])
		const allValidationErrors = ref([])

		provide("allValidationErrors", allValidationErrors)
		provide(
			"checkIfCategoryNameExistsInCurrentHierarchy",
			(categoryName, idx) => {
				return tempCategories.value.some(
					(c) => c.category_name == categoryName && c.idx != idx
				)
			}
		)

		const resources = ref(null)

		const saveInProgress = computed(() => {
			return resources.value.saveCategories.loading
		})
		const validateChanges = () => {
			return allValidationErrors.value.length == 0
		}
		const saveChanges = async () => {
			if (!validateChanges()) {
				this.$toast({
					title: "Validation Error",
					text: "Please fix the errors before saving",
					icon: "x",
					iconClasses: "text-red-500",
				})
				return
			}
			return await resources.value.saveCategories.submit({
				new_values: tempCategories.value.filter(
					(c) => !c.is_placeholder
				),
				old_values: resources.value.categories.data,
			})
		}

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
			editMode,
			isRoot,
			tempCategories,
			allValidationErrors,
			resources,
		}
	},
	mounted() {
		this.resources = this.$resources
	},
	computed: {
		categories() {
			if (!this.editMode) {
				this.list.loading = this.$resources.categories.loading
				this.list.data = this.$resources.categories.data || []
				return this.list.data
			} else {
				return this.tempCategories
			}
		},
	},
	watch: {
		editMode(newVal) {
			if (newVal) {
				this.tempCategories = JSON.parse(
					JSON.stringify(this.$resources.categories.data || [])
				)
				this.tempCategories.push({
					is_placeholder: true,
				})
			} else {
				this.allValidationErrors = []
			}
		},
	},
	resources: {
		categories() {
			const filters = this.categoryId
				? { parent_category: this.categoryId }
				: { is_group: true, parent_category: "" }
			filters.status = "Published"

			const fields = [
				"name",
				"category_name",
				"description",
				"parent_category",
				"is_group",
				"idx",
			]

			const cache = ["Categories", this.categoryId ? this.categoryId : ""]
			const limit = 999
			const order_by = "idx"
			return {
				cache,
				url: "helpdesk.api.kb.get_categories",
				params: {
					filters,
					fields,
					limit,
					order_by,
				},
				auto: true,
			}
		},
		saveCategories() {
			return {
				url: "helpdesk.api.kb.insert_new_update_existing_categories",
				onSuccess: () => {
					this.$resources.categories.reload()

					this.$toast({
						title: "Categories updated!!",
						icon: "check",
						iconClasses: "text-green-500",
					})
				},
				onError: (err) => {
					this.$toast({
						title: "Error while saving",
						text: err,
						icon: "x",
						iconClasses: "text-red-500",
					})
				},
			}
		},
	},
}
</script>
