<template>
	<div class="flex flex-row w-full">
		<SideBarMenu class="w-[173px] shrink-0 border-r" />
		<div class="grow text-[13px] font-normal p-5">
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
			<NewCategoryDialog 
				:show="showCreateNewCategoryDialog" 
				@close="showCreateNewCategoryDialog = false"
			/>
		</div>
	</div>
</template>

<script>
import ListManager from '@/components/global/ListManager.vue'
import SideBarMenu from '@/components/desk/knowledge_base/SideBarMenu.vue'
import ArticleList from '@/components/desk/knowledge_base/ArticleList.vue'
import { ErrorMessage } from 'frappe-ui'
import { ref } from '@vue/reactivity'
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
    NewCategoryDialog
},
	setup() {
		const showCreateNewCategoryDialog = ref(false)
		
		return {
			showCreateNewCategoryDialog,
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
	mounted() {
		const actions = [
			{ label: 'Add article', handler: () => { this.$router.push({name: 'NewArticle', query: { category: this.subCategory }}) }, appearance: 'primary', dropdown: [
				{ label: 'Add category', handler: () => {
					this.showCreateNewCategoryDialog = true
				}}
			] },
		]
		this.$event.emit('toggle_navbar_actions', ({type: 'Category', actions}))
		this.$event.emit('select_category',  (this.category && this.subCategory ) ? {name: this.subCategory, parent_category: this.category} : null)
	},
}
</script>