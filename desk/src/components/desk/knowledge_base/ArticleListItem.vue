<template>
	<div
		class="block select-none rounded-[6px] py-[7px] pl-[11px] pr-[9px]"
		:class="selected ? 'bg-blue-50 hover:bg-blue-100' : 'hover:bg-gray-50'"
	>
		<div v-if="article" class="group flex items-center text-base">
			<div class="w-[37px] h-[14px] flex items-center">
				<Input
					type="checkbox"
					@click="$emit('toggleSelect')"
					:checked="selected"
					class="cursor-pointer"
				/>
			</div>
			<div class="sm:w-5/12">
				<router-link
					:to="`/frappedesk/knowledge-base/articles/${article.name}`"
					class="flex items-center space-x-[8px]"
				>
					<div class="truncate max-w-fit lg:w-80 md:w-52 sm:w-40">
						{{ article.title }}
					</div>
				</router-link>
			</div>
			<div class="sm:w-2/12">
				<Badge
					class="text-base font-normal"
					:class="
						article.published ? 'text-green-600' : 'text-gray-600'
					"
					v-if="article"
					>{{ article.published ? "Publiished" : "Draft" }}</Badge
				>
			</div>
			<div class="sm:w-3/12">
				<Badge
					class="text-base font-normal"
					v-if="article.author_name"
					>{{ article.author_name }}</Badge
				>
			</div>
			<div class="sm:w-1/12">
				<div class="text-gray-600 font-normal" v-if="article.views">
					{{ article.views }}
				</div>
			</div>
			<div class="sm:w-1/12 font-normal">
				<div
					class="text-gray-600 font-normal text-right"
					v-if="article.modified"
				>
					{{
						$dayjs.shortFormating(
							$dayjs(article.modified).fromNow()
						)
					}}
				</div>
			</div>
		</div>
		<div class="transform translate-y-2" />
	</div>
</template>

<script>
import CustomIcons from "@/components/desk/global/CustomIcons.vue"
import { Avatar } from "frappe-ui"

export default {
	name: "ArticleListItem",
	props: ["article", "selected"],
	components: {
		CustomIcons,
		Avatar,
	},
}
</script>
