<template>
	<div class="flex flex-col space-y-[16px] pt-[12px] text-[13px] font-normal select-none">
		<div class="overflow-y-scroll flex flex-col space-y-[16px]" style="height: calc(100vh - 64px)">
			<div v-for="category in categories" :key="category.name">
				<div v-if="category.is_group" class="pl-[20px] pr-[6px]">
					<div 
						role="button" 
						class="flex flex-row items-center group space-x-2"
					>
						<div class="grow truncate" @click="expandCategory(category)">{{ category.name }}</div>
						<FeatherIcon @click="expandCategory(category)" :name="category.expanded ? 'chevron-up' : 'chevron-down'" class="h-4 w-4 shrink-0" />
					</div>
					<div v-if="category.expanded" class="pt-[16px] space-y-[16px] flex flex-col">
						<div v-for="subCategory in category.children" :key="subCategory.name">
							<router-link :to="`/frappedesk/knowledge-base/${subCategory.parent_category}/${subCategory.name}`"> 
								<div
									class="px-[12px] py-[4px] truncate rounded w-full" 
									:class="subCategory.name === selectedCategory.name ? 'bg-gray-50' : ''" 
								>
									{{ subCategory.name }} 
								</div>
							</router-link>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { ref } from 'vue'
import { FeatherIcon, Dropdown } from 'frappe-ui'

export default {
	components: {
		FeatherIcon,
		Dropdown,
	},
	setup() {       
		let categories = ref([])
		let selectedCategory = ref(null)

		return { categories, selectedCategory }
	},
	mounted() {
		this.$socket.on('list_update', (data) => {
			if (data['doctype'] == 'Category') {
				this.$resources.categories.list.reload()
			}
		});
		this.$event.on('select_category', (category) => {
			if (category) {
				this.selectedCategory = category
			}
		});
	},
	umbounted() {
		this.$event.off('select_category')
	},
	methods: {
		expandCategory(category) {
			if (category.children.length > 0) {
				category.expanded = !category.expanded
			} else {
				this.$toast({
					title: 'No Sub Categories',
					text: 'This category does not have any subcategories',
					icon: 'info',
					iconClasses: 'stroke-yellow-500',
					appearance: 'warning'
				})
			}
		}
	},
	resources: {
		categories() {
			return {
				type: 'list',
				doctype: 'Category',
				fields: ['is_group', 'parent_category', 'name', 'order'],
				onSuccess: (list) => {
					let categories = []
					list.forEach(category => {
						if (category.is_group) {
							categories.push({...category, children: [], expanded: false})
						}
					})
					list.forEach(category => {
						if (!category.is_group && category.parent_category && categories.find(c => c.name == category.parent_category)) {
							categories.find(c => c.name == category.parent_category).children.push(category)
						}
					})
					categories.sort(function(c1, c2){return c1.order - c2.order});
					for (let category of categories) {
						if (category.children.length > 0) {
							category.children.sort(function(c1, c2){return c1.order - c2.order});
							if (!this.selectedCategory) {
								this.selectedCategory = category.children[0]
								this.$router.push({path: `/frappedesk/knowledge-base/${this.selectedCategory.parent_category}/${this.selectedCategory.name}`})
							}
						}
					}

					this.categories = categories
					if (this.selectedCategory && this.selectedCategory.hasOwnProperty('parent_category')) {
						this.categories.find(cat => cat.name == this.selectedCategory.parent_category).expanded = true
					}
				}
			}
		}
	}
}
</script>