<template>
	<div class="flex flex-row" v-if="selectedCategory">
		<Categories 
			class="border-r w-[300px]" 
			:selectedCategory="selectedCategory"
		/>
		<Articles class="grow" :categoryId="selectedCategory" />
	</div>
</template>

<script>
import Categories from '@/components/desk/knowledge_base/Categories.vue'
import Articles from '@/components/desk/knowledge_base/Articles.vue'
import { ref } from 'vue'

export default {
	name: 'KnowledgeBase',
	components: {
		Categories,
		Articles
	},
	props: {
		categoryId: {
			type: String,
			default: ''
		}
	},
	setup(props) {
		const selectedCategory = ref(props.categoryId || '')

		return {
			selectedCategory
		}
	},
	resources: {
		categories() {
			return {
				method: 'frappe.client.get_list',
				params: {
					doctype: 'Category',
					fields: ['name']
				},
				auto: true,
				onSuccess: (res) => {
					if (!this.selectedCategory) {
						this.$router.push('/frappedesk/knowledge-base/' + res[0].name)
					}
				}
			}
		}
	}
}
</script>