<template>
	<div>
		<slot
			name="selector-main"
			:show="
				() => {
					showDialog = true
				}
			"
			:selectedCategoryName="selectedCategoryName"
		>
			<Input
				id="input"
				label="Category"
				@click="
					() => {
						showDialog = true
					}
				"
				placeholder="Choose Category"
				role="button"
				:value="selectedCategoryName"
			/>
		</slot>
		<Dialog
			:options="{ title: 'Select a Category' }"
			:show="showDialog"
			@close="
				() => {
					currentCategory = null
				}
			"
			v-model="showDialog"
		>
			<template #body-main>
				<div class="flex flex-col space-y-3 p-5">
					<div class="rounded border border-gray-200 p-2">
						<Breadcrumbs
							docType="Category"
							:docName="currentCategory?.name"
							:isRoot="!currentCategory"
							:overrideInteraction="
								(val, isRoot) => {
									if (isRoot) {
										currentCategory = null
									} else {
										currentCategory = val
									}
								}
							"
						>
						</Breadcrumbs>
					</div>
					<div class="h-[200px] overflow-y-auto">
						<div
							class="flex flex-col"
							v-if="categoriesInCurrentLevel.length > 0"
						>
							<div
								v-for="category in categoriesInCurrentLevel"
								:key="category.name"
							>
								<div
									@click="
										() => {
											currentCategory = category
										}
									"
									class="select-none py-3 flex flex-row items-center w-full rounded-sm px-2 border-gray-200 hover:bg-gray-50 border-b"
									role="button"
								>
									<div class="grow line-clamp-1 text-base">
										{{ category.category_name }}
									</div>
									<FeatherIcon
										name="chevron-right"
										class="h-5 w-5 stroke-gray-500"
									/>
								</div>
							</div>
						</div>
						<div v-else class="text-base text-gray-700">
							Its empty here
						</div>
					</div>
				</div>
			</template>
			<template #actions>
				<Button
					appearance="primary"
					:disabled="isRoot"
					@click="
						() => {
							showDialog = false
							$emit('selection', currentCategory)
							selectedCategoryName = currentCategory.category_name
							currentCategory = null
						}
					"
				>
					Select
				</Button>
			</template>
		</Dialog>
	</div>
</template>

<script>
import { ref } from "vue"
import Breadcrumbs from "@/components/global/kb/Breadcrumbs.vue"
import { FeatherIcon } from "frappe-ui"

export default {
	name: "CategorySelector",
	props: {
		selectedCategory: {
			type: String,
			default: null,
		},
	},
	components: {
		Breadcrumbs,
		FeatherIcon,
	},
	emits: ["category-selected", "update:show"],
	setup() {
		const currentCategory = ref(null)
		const showDialog = ref(false)

		const selectedCategoryName = ref(null)

		return {
			currentCategory,
			showDialog,
			selectedCategoryName,
		}
	},
	mounted() {
		this.fetchSubCategoriesInCategory(this.currentCategory?.name)

		// removes edit cursor from input when clicked on
		const input = document.getElementById("input")
		if (input) {
			input.addEventListener("focus", (event) => {
				input.blur()
			})
		}
	},
	computed: {
		isRoot() {
			return !this.currentCategory
		},
		categoriesInCurrentLevel() {
			return this.$resources.categoriesInCurrentLevel.data || []
		},
	},
	watch: {
		currentCategory(val) {
			this.fetchSubCategoriesInCategory(val?.name)
		},
	},
	resources: {
		categoriesInCurrentLevel() {
			return {
				url: "helpdesk.extends.client.get_list",
			}
		},
		selectedCategory() {
			if (!this.selectedCategory) return
			return {
				url: "frappe.client.get",
				params: {
					doctype: "HD Article Category",
					name: this.selectedCategory,
				},
				auto: true,
				onSuccess: (data) => {
					this.selectedCategoryName = data.category_name
				},
			}
		},
	},
	methods: {
		fetchSubCategoriesInCategory(category) {
			this.$resources.categoriesInCurrentLevel.fetch({
				doctype: "HD Article Category",
				fields: ["name", "category_name", "parent_category"],
				filters: {
					parent_category: category || "",
					status: "Published",
				},
				order_by: "idx desc",
				limit: 999,
			})
		},
	},
}
</script>
