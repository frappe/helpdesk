<template>
	<div class="rounded-[8px] border shadow-sm w-[220px] p-[16px] h-fit">
		<div class="flex flex-col space-y-[12px] text-base">
			<div class="font-semibold">Details</div>
			<div class="border-b w-full"></div>
			<a
				:href="`/${article.route}`"
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
				<FeatherIcon name="external-link" class="w-4" />
			</a>
			<div v-if="$resources.users.data" class="flex flex-col">
				<span class="block mb-2 text-sm leading-4 text-gray-700"
					>Author</span
				>
				<Autocomplete
					:options="
						$resources.users.data.map((x) => {
							return { label: x.full_name, value: x.name }
						})
					"
					placeholder="Choose author"
					:value="isNew ? user.user : article.author"
					@change="(item) => setArticleDetail('author', item.value)"
				/>
				<ErrorMessage :message="articleInputErrors.author" />
			</div>
			<div v-if="$resources.categories.data">
				<span class="block mb-2 text-sm leading-4 text-gray-700"
					>Category</span
				>
				<Autocomplete
					:options="
						$resources.categories.data.map((x) => {
							return { label: x.name, value: x.name }
						})
					"
					placeholder="Choose category"
					:value="
						isNew ? newArticleTempValues.category : article.category
					"
					@change="(item) => setArticleDetail('category', item.value)"
				>
					<template #no-result-found>
						<div
							role="button"
							class="hover:bg-gray-100 px-2.5 py-1.5 rounded-md text-base text-blue-500 font-semibold"
							@click="showCreateNewCategoryDialog = true"
						>
							Create new category
						</div>
					</template>
				</Autocomplete>
				<ErrorMessage :message="articleInputErrors.category" />
				<NewCategoryDialog
					:show="showCreateNewCategoryDialog"
					@close="showCreateNewCategoryDialog = false"
					@category-created="
						(category) => {
							this.$resources.categories.fetch().then(() => {
								this.setArticleDetail('category', category)
							})
						}
					"
					:redirectToCategory="false"
				/>
			</div>
			<Input
				type="textarea"
				label="Note"
				:value="article.note"
				@input="(val) => setArticleDetail('note', val)"
				:debounce="500"
				placeholder="Start typing to save..."
			/>
			<div
				class="flex flex-row items-center text-[12px] text-gray-700"
				v-if="!isNew"
			>
				<div class="flex flex-row items-center space-x-[6px]">
					<FeatherIcon name="eye" class="w-[16px] stroke-gray-500" />
					<div class="w-[28px] text-left">
						{{ article.views || 0 }}
					</div>
				</div>
				<div class="flex flex-row items-center space-x-[6px]">
					<FeatherIcon
						name="smile"
						class="w-[14px] stroke-gray-500"
					/>
					<div class="w-[28px] text-left">
						{{ article.likes || 0 }}
					</div>
				</div>
				<div class="flex flex-row items-center space-x-[6px]">
					<FeatherIcon
						name="frown"
						class="w-[14px] stroke-gray-500"
					/>
					<div class="w-[28px] text-left">
						{{ article.dislikes || 0 }}
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { FeatherIcon, ErrorMessage } from "frappe-ui"
import Autocomplete from "@/components/global/Autocomplete.vue"
import NewCategoryDialog from "@/components/desk/knowledge_base/NewCategoryDialog.vue"
import { inject, ref } from "@vue/runtime-core"

export default {
	name: "ArticleDetails",
	props: ["article", "articleResource", "isNew"],
	components: {
		FeatherIcon,
		ErrorMessage,
		Autocomplete,
		NewCategoryDialog,
	},
	setup() {
		const user = inject("user")
		const updateNewArticleInput = inject("updateNewArticleInput")
		const newArticleTempValues = inject("newArticleTempValues")
		const articleInputErrors = inject("articleInputErrors")
		const showCreateNewCategoryDialog = ref(false)

		return {
			user,
			updateNewArticleInput,
			newArticleTempValues,
			articleInputErrors,
			showCreateNewCategoryDialog,
		}
	},
	resources: {
		users() {
			return {
				method: "frappe.client.get_list",
				params: {
					doctype: "User",
					fields: ["name", "full_name"],
					filters: {
						enabled: 1,
					},
				},
				auto: true,
				onSuccess: (data) => {
					if (this.isNew) {
						this.setArticleDetail("author", this.user.user)
					}
				},
			}
		},
		categories() {
			return {
				method: "frappe.client.get_list",
				params: {
					doctype: "Category",
					fields: ["name"],
				},
				auto: true,
				onSuccess: (data) => {
					if (this.isNew) {
						this.setArticleDetail(
							"category",
							this.$route.query.category
								? this.$route.query.category
								: data.map((x) => x.name)[0]
						)
					}
				},
			}
		},
	},
	methods: {
		setArticleDetail(field, value) {
			if (!this.isNew) {
				let params = {}
				params[field] = value
				this.articleResource.setValue.submit(params)
			}
			{
				this.updateNewArticleInput({ field, value })
			}
		},
	},
}
</script>
