<template>
	<div class="text-[13px] font-normal p-5">
		<ListManager
			ref="articleList"
			:options="{
				doctype: 'Article',
				fields: [
					'title',
					'author',
					'author.full_name as author_name',
					'views',
					'modified'
				],
				filters: [['category', '=', subCategory]],
				order_by: 'modified desc',
				limit: 20
			}"
		>
			<template #body="{ manager }">
				<div>
					<ArticleList :manager="manager" />
				</div>
			</template>
		</ListManager>
		<Dialog :options="{title: 'New Category'}" :show="showCreateNewCategoryDialog" @close="() => { 
				showCreateNewCategoryDialog = false
			}"
		>
			<template #body-content>
				<div class="flex flex-col space-y-3">
					<div>
						<Input label="Category name" type="text" @change="(val) => { 
							newCategoryInputValues.name = val 
							newCategoryInputErrors.name = ''
						}" />
						<ErrorMessage :message="newCategoryInputErrors.name" />
					</div>
					<div>
						<Input label="Parent category" type="select" :options="parentCategories" @change="(val) => {
							newCategoryInputValues.parent = val
							newCategoryInputErrors.parent =	''
						}" />
						<ErrorMessage :message="newCategoryInputErrors.parent" />
					</div>
					<ErrorMessage :message="newCategoryInputErrors.others" />
				</div>
			</template>
			<template #actions>
				<div>
					<Button 
						:loading="$resources.createNewCategory.loading"
						appearance="primary" 
						@click="$resources.createNewCategory.submit({
							name: newCategoryInputValues.name,
							parent: newCategoryInputValues.parent
						})"
					>
						Add Category
					</Button>
				</div>
			</template>
		</Dialog>
	</div>
</template>

<script>
import ListManager from '@/components/global/ListManager.vue'
import ArticleList from '@/components/desk/knowledge_base/ArticleList.vue'
import { ErrorMessage } from 'frappe-ui'
import { ref } from '@vue/reactivity'

export default {
	name: 'KnowledgeBaseCategory',
	props: {
		category: {
			type: String,
			default: '',
		},
		subCategory: {
			type: String,
			default: '',
		},
	},
	components: {
		ListManager,
		ArticleList,
		ErrorMessage,
	},
	setup() {
		const showCreateNewCategoryDialog = ref(false)

		const newCategoryInputValues = ref({name: '', parent: 'none'})
		const newCategoryInputErrors = ref({name: '', parent: '', other: ''})
		
		return {
			showCreateNewCategoryDialog,
			newCategoryInputValues,
			newCategoryInputErrors
		}
	},
	computed: {
		parentCategories() {
			if (this.$resources.allParentCategories.data) {
				let categories = ['none']
				this.$resources.allParentCategories.data.forEach(category => {
					categories.push(category.name)
				})
				return categories
			} else {
				return []
			}
		} 
	},
	mounted() {
		this.$event.on('create_new_category', () => {
			this.showCreateNewCategoryDialog = true
		})
	},
	unmounted() {
		this.$event.off('create_new_category')
	},
	resources: {
		allParentCategories() {
			return {
				method: 'frappe.client.get_list',
				params: {
					doctype: 'Category',
					filters: {is_group: ['=', 1]},
					fields: ['name']
				},
				auto: true,
			}
		},
		createNewCategory() {
			return {
				method: 'frappe.client.insert',
				makeParams({ name, parent }) {
					return {
						doc: {
							doctype: 'Category',
							category_name: name,
							parent_category: parent === 'none' ? '' : parent,
							is_group: parent === 'none' ? 1 : 0,
						},
					}
				},
				validate(params) {
					if (!params.doc.category_name) {
						this.newCategoryInputErrors.name = 'Category name is required'
						return `Please enter category name`
					}
				},
				onSuccess() {
					this.showCreateNewCategoryDialog = false
					this.newCategoryInputValues = {}
				},
				onError() {
					this.showCreateNewCategoryDialog = false
					this.$toast({
						title: 'Error while creating category!',
						customIcon: 'circle-fail',
						appearance: 'danger',
					})
				}
			}
		}
	},
}
</script>