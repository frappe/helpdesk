<template>
	<div class="h-full">
		<div
			v-if="category.is_placeholder"
			class="border-2 border-dashed border-gray-400 rounded-md p-5 mr-4"
		>
			<div class="h-[130px]">
				<div
					class="my-auto flex items-center space-x-2 p-5 hover:bg-gray-50 h-full hover:cursor-pointer rounded-md group"
				>
					<div
						class="grow text-center text-gray-700 group-hover:text-gray-900"
					>
						Add Category
					</div>
				</div>
			</div>
		</div>
		<div
			v-else
			class="bg-white grow shadow rounded-md border p-5 group flex flex-row space-x-1 h-full"
			:class="editMode ? '' : 'cursor-pointer hover:shadow-md'"
		>
			<div class="flex flex-row items-center grow">
				<div
					class="grow flex flex-col space-y-2"
					:class="editMode ? 'h-[130px]' : ''"
				>
					<div class="flex flex-col">
						<input
							v-if="editMode"
							v-on-outside-click="
								() => {
									if (category.is_new) {
										onCategoryNameInput(
											category.category_name
										)
									}
								}
							"
							:placeholder="editMode ? 'Category name' : ''"
							ref="categoryName"
							type="text"
							:disabled="!editMode"
							class="border-none p-0 text-gray-900 text-xl focus:ring-0 font-semibold"
							:class="editMode ? '' : 'cursor-pointer'"
							:value="category.category_name"
							@input="onCategoryNameInput($event.target.value)"
						/>
						<div
							class="line-clamp-1 text-xl text-gray-900 font-semibold"
							v-else
						>
							{{ category.category_name }}
						</div>
						<ErrorMessage
							:message="validationErrors.category_name"
						/>
					</div>
					<div class="flex flex-col">
						<textarea
							v-if="editMode"
							ref="categoryDescription"
							rows="4"
							:placeholder="editMode ? 'Write a description' : ''"
							:disabled="!editMode"
							class="resize-none border-none p-0 text-base text-gray-500 focus:ring-0 line-clamp-4"
							:class="editMode ? '' : 'cursor-pointer'"
							:value="category.description"
							@input="onDescriptionInput($event.target.value)"
						/>
						<div
							class="h-[81px] line-clamp-4 text-base text-gray-500"
							v-else
						>
							{{ category.description }}
						</div>
						<ErrorMessage :message="validationErrors.description" />
					</div>
				</div>
			</div>
			<div
				v-if="editMode"
				class="w-[30px] h-full flex flex-col justify-between items-center"
			>
				<div class="flex flex-row-reverse">
					<CustomIcons
						name="drag-handle"
						class="w-4 h-4 handle cursor-grab"
					/>
				</div>
				<div class="flex flex-row-reverse" v-if="deletable">
					<Tooltip
						:class="
							dissableCategoryDeletion
								? 'cursor-not-allowed'
								: 'cursor-pointer'
						"
						placement="top"
					>
						<template #body>
							<div
								class="max-w-[30ch] rounded-lg border border-gray-100 bg-gray-800 px-2 py-1 text-center text-xs text-white shadow-xl"
							>
								{{
									dissableCategoryDeletion
										? "Cannot delete this category, it contains subcategories or articles"
										: "Delete"
								}}
							</div>
						</template>
						<Button
							:disabled="dissableCategoryDeletion"
							icon="trash"
							appearance="minimal"
							@click="$emit('delete')"
						/>
					</Tooltip>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { inject, ref } from "vue"
import { ErrorMessage, debounce } from "frappe-ui"
import CustomIcons from "@/components/desk/global/CustomIcons.vue"

export default {
	name: "CategoryCard",
	props: {
		category: {
			type: Object,
			required: true,
		},
		deletable: {
			type: Boolean,
			default: false,
		},
	},
	components: {
		CustomIcons,
		ErrorMessage,
	},
	setup() {
		const editable = inject("editable")
		const editMode = inject("editMode")
		const validationErrors = ref({
			category_name: "",
			description: "",
		})
		const checkIfCategoryNameExistsInCurrentHierarchy = inject(
			"checkIfCategoryNameExistsInCurrentHierarchy"
		)

		const allValidationErrors = inject("allValidationErrors")

		return {
			editable,
			editMode,
			validationErrors,
			checkIfCategoryNameExistsInCurrentHierarchy,
			allValidationErrors,
		}
	},
	mounted() {
		if (this.category.is_new) {
			this.focusOnCategoryNameInput()
		}
	},
	watch: {
		editMode(val) {
			if (!val) {
				this.validationErrors = {
					category_name: "",
					description: "",
				}
			}
		},
	},
	computed: {
		numberOfArticlesInCategory() {
			return this.category.is_new
				? 0
				: this.$resources.numberOfArticlesInCategory.data
		},
		numberOfSubCategoriesInCategory() {
			return this.category.is_new
				? 0
				: this.$resources.numberOfSubCategoriesInCategory.data
		},
		dissableCategoryDeletion() {
			return (
				this.numberOfArticlesInCategory > 0 ||
				this.numberOfSubCategoriesInCategory > 0
			)
		},
	},
	resources: {
		numberOfArticlesInCategory() {
			if (this.category.is_new) return
			return {
				method: "frappe.client.get_count",
				params: {
					doctype: "Article",
					filters: {
						category: this.category.name,
					},
				},
				auto: true,
			}
		},
		numberOfSubCategoriesInCategory() {
			if (this.category.is_new) return
			return {
				method: "frappe.client.get_count",
				params: {
					doctype: "Category",
					filters: {
						parent_category: this.category.name,
					},
				},
				auto: true,
			}
		},
	},
	methods: {
		updateVlidationErrors(errorType, error) {
			this.validationErrors[errorType] = error

			if (
				this.validationErrors.category_name ||
				this.validationErrors.description
			) {
				if (
					!this.allValidationErrors.some(
						(c) => c == this.category.name
					)
				) {
					this.allValidationErrors.push(this.category.name)
				}
			} else {
				// remove the category name from the array
				const index = this.allValidationErrors.indexOf(
					this.category.name
				)
				if (index > -1) {
					this.allValidationErrors.splice(index, 1)
				}
			}
		},
		focusOnCategoryNameInput() {
			this.$nextTick(() => {
				this.$refs.categoryName.focus()
			})
		},
		onCategoryNameInput: debounce(function (value) {
			this.category.category_name = value
			this.updateVlidationErrors("category_name", "")

			value = value.trim()
			if (!value) {
				this.updateVlidationErrors(
					"category_name",
					"Category name is required"
				)
			} else if (
				this.checkIfCategoryNameExistsInCurrentHierarchy(
					value,
					this.category.idx
				)
			) {
				this.updateVlidationErrors(
					"category_name",
					`${this.category.category_name} already exists.`
				)
			}
		}, 300),
		onDescriptionInput: debounce(function (value) {
			this.category.description = value
			this.validationErrors.description = ""
			// TODO: do validations if required
		}, 300),
	},
}
</script>
