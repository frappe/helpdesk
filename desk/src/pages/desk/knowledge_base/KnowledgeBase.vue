<template>
	<div class="flex flex-col" v-if="!$resources.categories.loading">
		<TopNavbar class="h-[52px] border-b" />
		<router-view class="grow" />
	</div>
</template>

<script>
import TopNavbar from '@/components/desk/knowledge_base/TopNavbar.vue'
import { provide, ref } from 'vue'

export default {
	name: 'KnowledgeBase',
	components: {
		TopNavbar,
	},
	setup() {
		const allCategories = ref([])
		provide('allCategories', allCategories)

		return {
			allCategories,
		}
	},
	resources: {
		categories() {
			return {
				method: 'frappe.client.get_list',
				params: {
					doctype: 'Category',
				},
				auto: true,
				onSuccess: (data) => {
					this.allCategories = data
				},
			}
		},
	}
}
</script>