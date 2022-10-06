<template>
	<div>
		<div
			class="bg-[#F7F7F7] group flex items-center h-[40px] text-base font-medium text-gray-500 py-[10px] px-[11px] rounded-[6px] select-none"
		>
			<div class="w-[37px] h-[14px]">
				<Input
					type="checkbox"
					@click="manager.selectAll()"
					:checked="manager.allItemsSelected"
					class="cursor-pointer mr-1 hover:visible"
				/>
			</div>
			<div
				class="sm:w-5/12 flex flex-row items-center space-x-[7px] cursor-pointer"
				@click="manager.toggleOrderBy('title')"
			>
				<span>Title</span>
				<div class="w-[10px]">
					<CustomIcons
						v-if="
							manager.options.order_by.split(' ')[0] === 'title'
						"
						:name="
							manager.options.order_by.split(' ')[1] === 'desc'
								? 'chevron-down'
								: 'chevron-up'
						"
						class="h-[6px] fill-gray-400 stroke-transparent"
					/>
				</div>
			</div>
			<div
				class="sm:w-2/12 flex flex-row items-center space-x-[6px] cursor-pointer"
				@click="manager.toggleOrderBy('published')"
			>
				<span>Status</span>
				<div class="w-[10px]">
					<CustomIcons
						v-if="
							manager.options.order_by.split(' ')[0] === 'views'
						"
						:name="
							manager.options.order_by.split(' ')[1] === 'desc'
								? 'chevron-down'
								: 'chevron-up'
						"
						class="h-[6px] fill-gray-400 stroke-transparent"
					/>
				</div>
			</div>
			<div
				class="sm:w-3/12 flex flex-row items-center space-x-[7px] cursor-pointer"
				@click="manager.toggleOrderBy('author')"
			>
				<span>Author</span>
				<div class="w-[10px]">
					<CustomIcons
						v-if="
							manager.options.order_by.split(' ')[0] === 'title'
						"
						:name="
							manager.options.order_by.split(' ')[1] === 'desc'
								? 'chevron-down'
								: 'chevron-up'
						"
						class="h-[6px] fill-gray-400 stroke-transparent"
					/>
				</div>
			</div>
			<div
				class="sm:w-1/12 flex flex-row items-center space-x-[6px] cursor-pointer"
				@click="manager.toggleOrderBy('views')"
			>
				<span>Views</span>
				<div class="w-[10px]">
					<CustomIcons
						v-if="
							manager.options.order_by.split(' ')[0] === 'views'
						"
						:name="
							manager.options.order_by.split(' ')[1] === 'desc'
								? 'chevron-down'
								: 'chevron-up'
						"
						class="h-[6px] fill-gray-400 stroke-transparent"
					/>
				</div>
			</div>
			<div
				class="sm:w-1/12 flex flex-row-reverse items-center cursor-pointer"
				@click="manager.toggleOrderBy('modified')"
			>
				<div class="w-[10px]">
					<CustomIcons
						v-if="
							manager.options.order_by.split(' ')[0] ===
							'modified'
						"
						:name="
							manager.options.order_by.split(' ')[1] === 'desc'
								? 'chevron-down'
								: 'chevron-up'
						"
						class="h-[6px] fill-gray-400 stroke-transparent"
					/>
				</div>
				<span class="px-[6px]">Modified</span>
			</div>
		</div>
		<div v-if="manager.list.length > 0">
			<div
				id="rows"
				class="flex flex-col overflow-scroll"
				:style="{
					height: viewportWidth > 768 ? 'calc(100vh - 132px)' : null,
				}"
			>
				<div
					v-for="(article, index) in manager.list"
					:key="article.name"
				>
					<ArticleListItem
						:class="index == 0 ? 'mt-[9px] mb-[2px]' : 'my-[2px]'"
						:article="article"
						@toggle-select="manager.select(article)"
						:selected="manager.itemSelected(article)"
					/>
				</div>
				<div class="pb-2">
					<Button
						v-if="manager.hasNextPage"
						@click="manager.nextPage()"
					>
						Load More
					</Button>
				</div>
			</div>
		</div>
		<div v-else>
			<div class="grid place-content-center w-full my-[100px]">
				<CustomIcons name="empty-list" class="h-12 w-12 mx-auto mb-2" />
				<div class="text-gray-500 mb-2 w-full text-center text-[16px]">
					No articles found
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import ArticleListItem from "./ArticleListItem.vue"
import CustomIcons from "../global/CustomIcons.vue"
import { inject } from "vue"

export default {
	name: "ArticleList",
	props: ["manager"],
	components: {
		ArticleListItem,
		CustomIcons,
	},
	setup() {
		const viewportWidth = inject("viewportWidth")

		return {
			viewportWidth,
		}
	},
	resources: {
		totalArticles() {
			return {
				method: "frappe.client.get_count",
				params: {
					doctype: "Article",
				},
				auto: true,
			}
		},
	},
}
</script>
