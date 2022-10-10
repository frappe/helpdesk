<template>
	<div class="flex flex-col h-full">
		<ListManager
			ref="articleList"
			:options="{
				doctype: 'Article',
				fields: ['title', 'status', 'views', 'author', 'modified'],
				order_by: 'modified desc',
				limit: 20,
			}"
		>
			<template #body="{ manager }">
				<ListViewer
					:manager="manager"
					:options="{
						fields: {
							title: {
								label: 'Title',
								width: '6',
								priority: 1,
							},
							status: {
								label: 'Status',
								width: '3',
								priority: 1,
							},
							views: {
								label: 'Views',
								width: '2',
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
						<LayoutSwitcher viewMode="List" />
					</template>
					<template #bulk-actions="{ selectedItems }">
						<div class="flex flex-row space-x-2">
							<Button @click="() => {}">Mark as Draft</Button>
							<Button @click="() => {}">Add to FAQ</Button>
							<Button @click="() => {}">Archive</Button>
						</div>
					</template>
					<template #actions>
						<div class="flex flex-row space-x-2">
							<Button> Action 1 </Button>
							<Button> Action 2 </Button>
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
	},
}
</script>
