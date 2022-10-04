<template>
	<div class="px-[16px]">
		<ListManager
			ref="categories"
			:options="{
				doctype: 'Category',
				fields: ['name', 'description', 'category_name'],
				limit: 100,
				order_by: 'idx desc',
			}"
		>
			<template #body="{ manager }">
				<div class="flex flex-col">
					<div
						class="pt-[26px] pb-[8px] flex flex-row justify-between items-center"
					>
						<div class="grow">Categories</div>
						<div>
							<div class="flex items-center space-x-3">
								<div
									class="stroke-blue-500 fill-blue-500 w-0 h-0 block"
								></div>
								<div
									class="cursor-pointer p-1 hover:bg-gray-200 bg-gray-100 rounded"
									@click="showNewCategoryDialog = true"
								>
									<FeatherIcon name="plus" class="h-3 w-3" />
								</div>
							</div>
						</div>
					</div>
					<div v-if="!manager.loading">
						<div class="flex flex-col">
							<div
								v-for="(category, index) in manager.list"
								:key="category.name"
							>
								<div>
									<CategoryCard
										:category="category"
										:isSelected="
											category.name == selectedCategory
										"
										@updated="
											() => {
												$refs.categories.manager.reload()
											}
										"
										@deleted="
											() => {
												if (
													category.name ==
													selectedCategory
												) {
													$router.push(
														'/frappedesk/knowledge-base'
													)
												}
												$refs.categories.manager.reload()
											}
										"
									/>
									<div
										class="mx-[10px]"
										:class="
											index < manager.list.length - 1
												? 'border-b'
												: ''
										"
									></div>
								</div>
							</div>
						</div>
					</div>
				</div>
			</template>
		</ListManager>
		<NewCategoryDialog
			:show="showNewCategoryDialog"
			@close="
				() => {
					showNewCategoryDialog = false
				}
			"
			@category-created="
				() => {
					$refs.categories.manager.reload()
				}
			"
		/>
	</div>
</template>

<script>
import ListManager from "@/components/global/ListManager.vue"
import CategoryCard from "@/components/desk/knowledge_base/CategoryCard.vue"
import { FeatherIcon } from "frappe-ui"
import { ref } from "vue"
import NewCategoryDialog from "@/components/desk/knowledge_base/NewCategoryDialog.vue"

export default {
	name: "Categories",
	components: {
		ListManager,
		FeatherIcon,
		CategoryCard,
		NewCategoryDialog,
	},
	props: {
		selectedCategory: {
			type: String,
			default: "",
		},
	},
	setup() {
		const showNewCategoryDialog = ref(false)

		return {
			showNewCategoryDialog,
		}
	},
}
</script>
