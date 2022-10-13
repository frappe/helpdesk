<template>
	<div class="flex flex-col h-full">
		<ListManager
			ref="articleList"
			:options="{
				doctype: 'Article',
				fields: [
					'title',
					'status',
					'views',
					'author',
					'modified',
					'category.category_name as category_name',
				],
				order_by: 'modified desc',
				limit: 20,
				filters: { status: ['!=', 'Archived'] },
			}"
		>
			<template #body="{ manager }">
				<ListViewer
					:manager="manager"
					:options="{
						showFilterBox: false,
						fields: {
							title: {
								label: 'Title',
								width: '5',
								priority: 1,
							},
							category_name: {
								label: 'Category',
								width: '3',
								priority: 1,
							},
							status: {
								label: 'Status',
								width: '2',
								priority: 1,
							},
							views: {
								label: 'Views',
								width: '1',
								priority: 3,
							},
							modified: {
								label: 'Modified',
								width: '1',
								priority: 2,
								align: 'right',
							},
						},
					}"
					@add-item="
						() => {
							$router.push('/frappedesk/kb/articles/new')
						}
					"
					class="text-base"
				>
					<template #top-sub-section-1>
						<LayoutSwitcher viewMode="List" />
					</template>
					<template #bulk-actions="{ selectedItems }">
						<div class="flex flex-row space-x-2">
							<CategorySelector
								@selection="
									(category) => {
										$resources.moveArticlesToCategory
											.submit({
												articles:
													Object.keys(selectedItems),
												category: category.name,
											})
											.then(() => {
												manager.unselect()
											})
									}
								"
							>
								<template #selector-main="{ show }">
									<Button @click="show">Move to</Button>
								</template>
							</CategorySelector>
							<Dropdown
								placement="right"
								:options="[
									{
										label: 'Draft',
										handler: () => {
											$resources.setStatusForArticles
												.submit({
													articles:
														Object.keys(
															selectedItems
														),
													status: 'Draft',
												})
												.then(() => {
													manager.unselect()
												})
										},
									},
									{
										label: 'Published',
										handler: () => {
											$resources.setStatusForArticles
												.submit({
													articles:
														Object.keys(
															selectedItems
														),
													status: 'Published',
												})
												.then(() => {
													manager.unselect()
												})
										},
									},
								]"
							>
								<template v-slot="{ toggleDropdown }">
									<Button
										:loading="
											$resources.setStatusForArticles
												.loading
										"
										icon-right="chevron-down"
										class="ml-2"
										@click="toggleDropdown"
									>
										Mark as
									</Button>
								</template>
							</Dropdown>
							<!-- <Button @click="() => {}">Add to FAQ</Button> -->
							<Button
								@click="
									() => {
										$resources.deleteArticles
											.submit({
												articles:
													Object.keys(selectedItems),
											})
											.then(() => {
												manager.unselect()
												manager.reload()
											})
									}
								"
								>Delete</Button
							>
						</div>
					</template>
					<template #actions>
						<div class="flex flex-row space-x-2">
							<!-- Add actions here -->
						</div>
					</template>
					<template #field-title="{ value, row }">
						<router-link
							:to="{
								path: `/frappedesk/kb/articles/${row.name}`,
							}"
							class="cursor-pointer hover:text-gray-900 text-gray-600"
							>{{ value }}</router-link
						>
					</template>
					<template #field-status="{ value }">
						<div
							:class="
								value === 'Published'
									? 'text-green-500'
									: 'text-gray-500'
							"
						>
							{{ value }}
						</div>
					</template>
					<template #field-views="{ value }">
						<div>{{ value }}</div>
					</template>
					<template #field-modified="{ value }">
						<div>
							{{
								$dayjs.shortFormating(
									$dayjs(value).fromNow(),
									false
								)
							}}
						</div>
					</template>
				</ListViewer>
			</template>
		</ListManager>
	</div>
</template>

<script>
import ListManager from "@/components/global/ListManager.vue"
import ListViewer from "@/components/global/ListViewer.vue"
import LayoutSwitcher from "@/components/global/kb/LayoutSwitcher.vue"
import CategorySelector from "@/components/desk/kb/CategorySelector.vue"
import { Dropdown } from "frappe-ui"

export default {
	name: "Articles",
	props: {
		categoryId: {
			type: String,
			default: "",
		},
	},
	components: {
		ListManager,
		ListViewer,
		LayoutSwitcher,
		CategorySelector,
		Dropdown,
	},
	resources: {
		moveArticlesToCategory() {
			return {
				method: "frappedesk.api.kb.move_articles_to_category",
			}
		},
		setStatusForArticles() {
			return {
				method: "frappedesk.api.kb.set_status_for_articles",
			}
		},
		deleteArticles() {
			return {
				method: "frappedesk.api.kb.delete_articles",
			}
		},
	},
}
</script>
