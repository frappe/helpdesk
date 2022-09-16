<template>
	<div class="flex flex-row w-full">
		<SideBarMenu class="w-[173px] shrink-0 border-r"/>
		<div class="grow text-[13px] font-normal p-5">
			<ListManager
				v-if="subCategory"
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
				@selection="updateActions()"
			>
				<template #body="{ manager }">
					<div v-if="!manager.loading">
						<div v-if="manager.list.length > 0">
							<ArticleList :manager="manager" />
						</div>
						<div v-else>
							<div class="grid place-content-center w-full mt-10">
								<CustomIcons name="empty-list" class="h-12 w-12 mx-auto mb-2" />
								<div class="text-gray-500 mb-2 w-full text-center text-[16px]">No articles found</div>
								<div class="mt-4 mx-auto">
									<Button @click="() => { $router.push({name: 'NewArticle', query: { category: subCategory }}) }" appearance="primary">Add Article</Button>
								</div>
							</div>
						</div>
					</div>
				</template>
			</ListManager>
			<div v-else-if="category">
				<div class="grid place-content-center w-full mt-10">
					<CustomIcons name="empty-list" class="h-12 w-12 mx-auto mb-2" />
					<div class="text-gray-500 mb-2 w-full text-center text-[16px]">No sub categories found</div>
					<div class="mx-auto space-x-2 mt-4">
						<Button @click="() => { showCreateNewCategoryDialog = true }" appearance="primary">{{ allCategories.length > 1 ? 'Add Sub Category' : 'Add Category'}}</Button>
					</div>
				</div>
			</div>
			<ErrorMessage v-else message="Something went wrong"/>
			<NewCategoryDialog 
				:show="showCreateNewCategoryDialog" 
				@close="showCreateNewCategoryDialog = false"
				:newCategoryParent="category"
			/>
			<Dialog 
				:options="{
					title: `Deleting ${documentsToDeleteStr}`, 
					message: `Do you really want to delete this ${doctypeToDelete.toLowerCase()}(s)?`,
					actions: [
						{
							label: 'Delete',
							appearance: 'danger',
							handler: () => {
								$resources.deleteDoc.submit({doctype: doctypeToDelete, items: JSON.stringify(documentsToDelete)})
							}
						},
						{
							label: 'Cancel',
							appearance: 'secondary',
							handler: () => { showDeleteDialog = false }
						},
					]
				}" 
				:show="showDeleteDialog" 
				@close="showDeleteDialog = false"
			/>
		</div>
	</div>
</template>

<script>
import ListManager from '@/components/global/ListManager.vue'
import SideBarMenu from '@/components/desk/knowledge_base/SideBarMenu.vue'
import ArticleList from '@/components/desk/knowledge_base/ArticleList.vue'
import CustomIcons from '@/components/desk/global/CustomIcons.vue'
import { ErrorMessage } from 'frappe-ui'
import { ref, inject } from 'vue'
import NewCategoryDialog from '@/components/desk/knowledge_base/NewCategoryDialog.vue'

export default {
	name: 'Category',
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
    SideBarMenu,
	CustomIcons,
    NewCategoryDialog
},
	setup() {
		const showCreateNewCategoryDialog = ref(false)
		const showDeleteDialog = ref(false)

		const documentsToDelete = ref([])
		const doctypeToDelete = ref('')

		const allCategories = inject('allCategories')
		
		return {
			showCreateNewCategoryDialog,
			showDeleteDialog,
			documentsToDelete,
			doctypeToDelete,
			allCategories
		}
	},
	watch: {
		subCategory(val) {
			this.$refs.articleList?.manager?.update({
				filters: [['category', '=', val]],
			})
			this.$event.emit('select_category', {name: this.subCategory, parent_category: this.category})
		}
	},
	computed: {
		documentsToDeleteStr() {
			let str = ''
			this.documentsToDelete.forEach((doc, index) => {
				str += doc
				if (index !== this.documentsToDelete.length - 1) {
					str += ', '
				}
			})
			return str
		}
	},
	mounted() {
		const updateBaseActions = () => {
			const actions = this.getBaseActions()
			this.$event.emit('toggle_navbar_actions', ({type: 'Category', actions}))
		}

		updateBaseActions()
		this.$event.emit('select_category',  (this.category && this.subCategory ) ? {name: this.subCategory, parent_category: this.category} : null)
		
		this.$event.on('select_category', () => {
			updateBaseActions()
		})
	},
	resources: {
		deleteDoc() {
			return {
				method: 'frappe.desk.reportview.delete_items',
				onSuccess: () => {
					if (this.doctypeToDelete == 'Category') {
						this.$router.push({name: 'Category', params: {category: this.category}}).then(() => {
							this.$router.go()
						})
					} else {
						this.$router.push({name: 'SubCategory', params: {category: this.category, subCategory: this.subCategory}}).then(() => {
							this.$router.go()
						})
					}
					this.showDeleteDialog = false
				}
			}
		}
	},
	methods: {
		updateActions() {
			const selectedArticles = this.$refs.articleList?.manager?.selectedItems
			const actions = this.getBaseActions()
			if (Object.keys(selectedArticles).length > 0) {
				actions.unshift({
					label: 'Delete',
					appearance: 'secondary',
					handler: () => {
						this.doctypeToDelete = 'Article';
						this.documentsToDelete = Object.values(selectedArticles).map(x => x.name)
						this.showDeleteDialog = true
					}
				})
			}
			this.$event.emit('toggle_navbar_actions', ({type: 'Category', actions}))
		},
		getBaseActions() {
			let actions = []
			if (this.subCategory) {
				actions = [
					{ 
						label: 'Add article', 
						handler: () => { this.$router.push({name: 'NewArticle', query: { category: this.subCategory }}) }, 
						appearance: 'primary', 
						dropdown: [
							{ 
								label: 'Add category', 
								handler: () => {
									this.showCreateNewCategoryDialog = true
								}
							},
						] 
					},
				]
			} else if (this.category) {
				actions = [
					{ 
						label: 'Add category', 
						handler: () => {
							this.showCreateNewCategoryDialog = true
						},
						appearance: 'primary'
					},
				]
			}
			return actions
		}
	}
}
</script>