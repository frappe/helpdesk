<template>
	<div
		class="flex flex-row group cursor-pointer"
		:class="isSelected ? 'bg-gray-50' : ''"
	>
		<router-link :to="`/frappedesk/knowledge-base/${category.name}`">
			<div class="select-none flex flex-col py-[16px] px-[10px] rounded">
				<a
					:href="href"
					@click="navigate"
					class="text-[14px] font-normal grow"
				>
					{{ category.name }}
				</a>
				<a
					:href="href"
					@click="navigate"
					class="text-[12px] h-[40px] line-clamp-2 w-[223px]"
				>
					{{ category.description }}
				</a>
			</div>
		</router-link>
		<div>
			<div class="mt-[16px] invisible group-hover:visible">
				<a category_name="Edit">
					<FeatherIcon
						name="edit-2"
						class="h-[14px] w-[14px] hover:stroke-2 stroke-1"
						@click="
							() => {
								showEditDialog = true
							}
						"
					/>
				</a>
			</div>
		</div>
		<EditCategoryDialog
			:categoryToEdit="category"
			:show="showEditDialog"
			@close="
				() => {
					showEditDialog = false
				}
			"
			@updated="
				() => {
					$emit('updated')
				}
			"
			@deleted="
				() => {
					$emit('deleted')
				}
			"
		/>
	</div>
</template>
<script>
import { FeatherIcon } from "frappe-ui"
import EditCategoryDialog from "@/components/desk/knowledge_base/EditCategoryDialog.vue"
import { ref } from "vue"

export default {
	name: "CategoryCard",
	components: {
		FeatherIcon,
		EditCategoryDialog,
	},
	props: {
		category: {
			type: Object,
			default: () => ({}),
		},
		isSelected: {
			type: Boolean,
			default: false,
		},
	},
	setup() {
		const showEditDialog = ref(false)

		return {
			showEditDialog,
		}
	},
}
</script>
