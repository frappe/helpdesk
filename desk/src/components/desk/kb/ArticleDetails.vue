<template>
	<div class="flex flex-col rounded shadow p-5 text-base space-y-[12px]">
		<div class="font-semibold">Details</div>
		<div class="border-b w-full"></div>
		<RouterLink
			:to="`/knowledge-base/articles/${article.name}`"
			target="_blank"
			v-if="article.published_on"
			class="flex flex-row justify-between items-center"
		>
			<div>
				Published
				{{
					$dayjs.shortFormating(
						$dayjs(article.published_on).fromNow(),
						true
					)
				}}
			</div>
			<FeatherIcon name="external-link" class="h-4 w-4" />
		</RouterLink>
		<div v-if="$resources.users.data" class="flex flex-col">
			<span class="block mb-2 text-sm leading-4 text-gray-700">
				Author
			</span>
			<Autocomplete
				:options="
					$resources.users.data.map((x) => {
						return { label: x.name, value: x.name }
					})
				"
				placeholder="Choose author"
				:value="isNew ? articleTempValues?.author : article.author"
				@change="
					(item) => {
						if (!item) return
						setArticleDetail('author', item.value)
					}
				"
			/>
			<ErrorMessage :message="articleInputErrors.author" />
		</div>
		<div>
			<CategorySelector
				:selectedCategory="
					isNew ? articleTempValues?.category : article.category
				"
				@selection="
					(category) => {
						setArticleDetail('category', category.name)
					}
				"
			/>
			<ErrorMessage :message="articleInputErrors.category" />
		</div>
		<div
			class="flex flex-row items-center text-sm text-gray-700"
			v-if="!isNew"
		>
			<div class="flex flex-row items-center space-x-[6px]">
				<FeatherIcon name="eye" class="w-[16px] stroke-gray-500" />
				<div class="w-[28px] text-left">
					{{ article.views || 0 }}
				</div>
			</div>
			<div class="flex flex-row items-center space-x-[6px]">
				<FeatherIcon name="smile" class="w-[14px] stroke-gray-500" />
				<div class="w-[28px] text-left">
					{{ article.helpful || 0 }}
				</div>
			</div>
			<div class="flex flex-row items-center space-x-[6px]">
				<FeatherIcon name="frown" class="w-[14px] stroke-gray-500" />
				<div class="w-[28px] text-left">
					{{ article.not_helpful || 0 }}
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { FeatherIcon, ErrorMessage } from "frappe-ui"
import Autocomplete from "@/components/global/Autocomplete.vue"
import { inject } from "vue"
import CategorySelector from "@/components/desk/kb/CategorySelector.vue"

export default {
	name: "ArticleDetails",
	props: {
		article: {
			type: Object,
			default: null,
		},
		articleResource: {
			type: Object,
			default: null,
		},
		isNew: {
			type: Boolean,
			default: false,
		},
	},
	components: {
		FeatherIcon,
		ErrorMessage,
		Autocomplete,
		CategorySelector,
	},
	setup() {
		const updateArticleTempValues = inject("updateArticleTempValues")
		const articleTempValues = inject("articleTempValues")
		const articleInputErrors = inject("articleInputErrors")

		return {
			updateArticleTempValues,
			articleTempValues,
			articleInputErrors,
		}
	},
	resources: {
		users() {
			return {
				url: "helpdesk.extends.client.get_list",
				params: {
					doctype: "User",
					fields: ["name", "full_name"],
					filters: {
						enabled: 1,
					},
					limit: 9999,
				},
				auto: true,
			}
		},
	},
	methods: {
		setArticleDetail(field, value) {
			if (!this.isNew) {
				let params = {}
				params[field] = value
				this.articleResource.setValue.submit(params).then(() => {
					if (field === "category") {
						// This Refreshes the breadcrumbs
						// TODO: Find a better way to do this
						this.$router.go()
					}
				})
			} else {
				this.updateArticleTempValues({ field, value })
			}
		},
	},
}
</script>
