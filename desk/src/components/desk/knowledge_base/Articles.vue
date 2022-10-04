<template>
	<div class="flex flex-col h-screen">
		<div class="grow flex flex-col text-[13px] font-normal px-[16px]">
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
					limit: 20,
				}"
			>
				<template #body="{ manager }">
					<div class="flex flex-col">
						<div class="h-[72px] py-[22px] flow-root">
							<div class="float-left">
								<div
									class="my-1 text-gray-600 flex flex-row items-center space-x-[50px] select-none"
								>
									<div
										class="flex flex-row space-x-2 items-center"
									>
										<div class="text-[14px]">Published</div>
										<div
											class="rounded-lg px-[10px] py-[3px] bg-blue-50 text-[13px]"
										>
											{{
												$resources
													.publishedArticlesCount.data
											}}
										</div>
									</div>
									<div
										class="flex flex-row space-x-2 items-center"
									>
										<div class="text-[14px]">Draft</div>
										<div
											class="rounded-lg px-[10px] py-[3px] bg-gray-50 text-[13px]"
										>
											{{
												$resources.draftArticlesCount
													.data
											}}
										</div>
									</div>
								</div>
							</div>
							<div class="float-right">
								<div
									class="flex flex-row space-x-2"
									v-if="
										Object.keys(manager.selectedItems)
											.length == 0
									"
								>
									<router-link
										:to="{
											name: 'NewArticle',
											query: { category: categoryId },
										}"
									>
										<Button
											icon-left="plus"
											appearance="primary"
											>Add Article</Button
										>
									</router-link>
								</div>
								<div v-else class="flex flex-row space-x-2">
									<Button
										appearance="secondary"
										@click="
											() => {
												changeArticleStatus(
													manager.selectedItems,
													false
												)
											}
										"
									>
										Mark as Draft
									</Button>
									<Button
										appearance="primary"
										@click="
											() => {
												changeArticleStatus(
													manager.selectedItems,
													true
												)
											}
										"
									>
										Publish
									</Button>
								</div>
							</div>
						</div>
						<div v-if="!manager.loading">
							<ArticleList :manager="manager" />
						</div>
					</div>
				</template>
			</ListManager>
		</div>
	</div>
</template>

<script>
import ListManager from "@/components/global/ListManager.vue"
import ArticleList from "@/components/desk/knowledge_base/ArticleList.vue"
import CustomIcons from "@/components/desk/global/CustomIcons.vue"
import { ErrorMessage, FeatherIcon } from "frappe-ui"

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
		ArticleList,
		ErrorMessage,
		CustomIcons,
		FeatherIcon,
	},
	setup() {},
	computed: {
		documentsToDeleteStr() {
			let str = ""
			this.documentsToDelete.forEach((doc, index) => {
				str += doc
				if (index !== this.documentsToDelete.length - 1) {
					str += ", "
				}
			})
			return str
		},
	},
	methods: {
		changeArticleStatus(items, publish = false) {
			const docs = []
			Object.keys(items).forEach((item) => {
				docs.push({
					doctype: "Article",
					docname: item,
					published: publish,
				})
			})
			this.$resources.markArticlesAsDraft.submit({
				docs: JSON.stringify(docs),
			})
		},
	},
	resources: {
		deleteDoc() {
			return {
				method: "frappe.desk.reportview.delete_items",
				onSuccess: () => {},
			}
		},
		publishedArticlesCount() {
			return {
				method: "frappe.client.get_count",
				params: {
					doctype: "Article",
					filters: [
						["category", "=", this.categoryId],
						["published", "=", 1],
					],
				},
				auto: true,
			}
		},
		draftArticlesCount() {
			return {
				method: "frappe.client.get_count",
				params: {
					doctype: "Article",
					filters: [
						["category", "=", this.categoryId],
						["published", "=", 0],
					],
				},
				auto: true,
			}
		},
		markArticlesAsDraft() {
			return {
				method: "frappe.client.bulk_update",
				onSuccess: () => {
					this.$resources.publishedArticlesCount.fetch()
					this.$resources.draftArticlesCount.fetch()
					this.$toast({
						title: "Articles updated!!",
						customIcon: "circle-check",
						appearance: "success",
					})
					this.$refs.articleList.manager.reload()
				},
				onError: (err) => {
					this.$toast({
						title: "Something went wrong!!",
						text: err,
						customIcon: "circle-fail",
						appearance: "danger",
					})
				},
			}
		},
	},
}
</script>
