<template>
	<div class="flex flex-col h-full">
		<ListManager
			ref="categoryList"
			:options="{
				doctype: 'Category',
				fields: [
					'category_name',
					'is_group',
					'parent_category',
					'modified',
				],
				order_by: 'modified desc',
				filters: { status: 'Published' },
				limit: 20,
			}"
		>
			<template #body="{ manager }">
				<ListViewer
					:manager="manager"
					:options="{
						fields: {
							category_name: {
								label: 'Name',
								width: '6',
								priority: 1,
							},
							parent_category: {
								label: 'Parent',
								width: '5',
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
					class="text-base"
				>
					<template #top-sub-section-1>
						<LayoutSwitcher
							viewMode="List"
							selectedList="Categories"
						/>
					</template>
					<template #bulk-actions="{ selectedItems }">
						<div class="flex flex-row space-x-2">
							<Button @click="() => {}">Do Something 1</Button>
							<Button @click="() => {}">Do Something 2</Button>
						</div>
					</template>
					<template #actions>
						<div class="flex flex-row space-x-2">
							<Button> Action 1 </Button>
							<Button> Action 2 </Button>
						</div>
					</template>
					<template #field-category_name="{ value, row }">
						<router-link
							:to="{
								path: `/frappedesk/kb/categories/${row.name}`,
							}"
							class="cursor-pointer hover:text-gray-900 text-gray-600"
							>{{ value }}</router-link
						>
					</template>
					<template #field-parent="{ value }">
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

export default {
	name: "Categories",
	components: {
		ListManager,
		ListViewer,
		LayoutSwitcher,
	},
}
</script>
