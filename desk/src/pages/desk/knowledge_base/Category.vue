<template>
	<div class="flex flex-col h-screen">
		<div class="grow flex flex-col border-t text-[13px] font-normal px-[16px]">
			<div class="h-[72px] py-[22px] flow-root">
				<div class="float-left">
					<router-link
						to="/frappedesk/knowledge-base"
						class="my-1 text-[12px] text-gray-600 stroke-gray-600 flex flex-row items-center space-x-1 hover:text-gray-700 hover:stroke-gray-700 select-none"
						role="button"
					>
						<FeatherIcon name="arrow-left" class="w-[13px] h-[13px]" />
						<div> Back to Knowledge Base </div>
					</router-link>
				</div>
				<div class="float-right">
					<Button icon-left="plus" appearance="primary" @click="() => {}">Add Article</Button>
				</div>
			</div>
			<ListManager
				ref="articleList"
				:options="{
					doctype: 'Article',
					fields: [
						'title',
						'author',
						'author.user_image as author_image',
						'author.full_name as author_name',
						'views',
						'modified',
						'published',
					],
					filters: [['category', '=', categoryId]],
					order_by: 'modified desc',
					limit: 20
				}"
			>
				<template #body="{ manager }">
					<div v-if="!manager.loading">
						<div v-if="manager.list.length > 0">
							<ArticleList :manager="manager" />
						</div>
						<div v-else>
							<div class="grid place-content-center w-full my-[100px]">
								<CustomIcons name="empty-list" class="h-12 w-12 mx-auto mb-2" />
								<div class="text-gray-500 mb-2 w-full text-center text-[16px]">No articles found</div>
							</div>
						</div>
					</div>
				</template>
			</ListManager>
		</div>
	</div>
</template>

<script>
import ListManager from '@/components/global/ListManager.vue'
import ArticleList from '@/components/desk/knowledge_base/ArticleList.vue'
import CustomIcons from '@/components/desk/global/CustomIcons.vue'
import { ErrorMessage, FeatherIcon } from 'frappe-ui'

export default {
	name: 'Categories',
	props: {
		categoryId: {
			type: String,
			default: '',
		},
	},
	components: {
		ListManager,
		ArticleList,
		ErrorMessage,
		CustomIcons,
		FeatherIcon
	},
	setup() {
		
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
	resources: {
		deleteDoc() {
			return {
				method: 'frappe.desk.reportview.delete_items',
				onSuccess: () => {}
			}
		}
	},
}
</script>