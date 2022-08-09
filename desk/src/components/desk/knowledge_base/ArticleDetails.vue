<template>
	<div class="rounded-[8px] border shadow-sm w-[220px] p-[16px] h-fit">
		<div class="flex flex-col space-y-[12px] text-base">
			<div class="font-semibold">Details</div>
			<div class="border-b w-full"></div>
			<div v-if="article.published_on" class="flex flex-row justify-between items-center">
				<div>Published {{ $dayjs.shortFormating($dayjs(article.published_on).fromNow()) }} ago</div>
				<a :href="`/${article.route}`" target="_blank">
					<FeatherIcon name="external-link" class="w-4" />
				</a>
			</div>
			<Input v-if="!$resources.users.loading" type="select" label="Author" :value="isNew ? user.user : article.author" @input="(val) => setArticleDetail('author', val)" :options="$resources.users.data.map(x => x.name)" />
			<Input v-if="!$resources.categories.loading" type="select" label="Category" :value="isNew ? newArticleTempValues.category : article.category" @input="(val) => setArticleDetail('category', val)" :options="$resources.categories.data.map(x => x.name)" />
			<Input type="textarea" label="Note" :value="article.note" @input="(val) => setArticleDetail('note', val)" :debounce="500" placeholder="Start typing to save..." />
			<div class="flex flex-row items-center text-[12px] text-gray-700" v-if="!isNew">
				<div class="flex flex-row items-center space-x-[6px]">
					<FeatherIcon name="eye" class="w-[16px] stroke-gray-500" />
					<div class="w-[28px] text-left">{{ article.views || 0 }}</div>
				</div>
				<div class="flex flex-row items-center space-x-[6px]">
					<FeatherIcon name="smile" class="w-[14px] stroke-gray-500" />
					<div class="w-[28px] text-left">{{ article.likes || 0 }}</div>
				</div>
				<div class="flex flex-row items-center space-x-[6px]">
					<FeatherIcon name="frown" class="w-[14px] stroke-gray-500" />
					<div class="w-[28px] text-left">{{ article.dislikes || 0 }}</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import { FeatherIcon } from 'frappe-ui'
import CustomComboboxInput from '@/components/global/CustomComboboxInput.vue'
import { inject } from '@vue/runtime-core'

export default {
	name: 'ArticleDetails',
	props: ['article', 'articleResource', 'isNew'],
	components: {
		FeatherIcon,
		CustomComboboxInput
	},
	setup() {
		const user = inject('user')
		const updateNewArticleInput = inject('updateNewArticleInput')
		const newArticleTempValues = inject('newArticleTempValues')

		return {
			user,
			updateNewArticleInput,
			newArticleTempValues
		}
	},
	resources: {
		users() {
			return {
				method: 'frappe.client.get_list',
				params: {
					doctype: 'User',
					fields: ['name', 'full_name'],
					filters: {
						enabled: 1
					}
				},
				auto: true,
				onSuccess: (data) => {
					if (this.isNew) {
						this.setArticleDetail('author', this.user.user)
					}
				}
			}
		},
		categories() {
			return {
				method: 'frappe.client.get_list',
				params: {
					doctype: 'Category',
					fields: ['name'],
					filters: {is_group: ['=', 0]},
				},
				auto: true,
				onSuccess: (data) => {
					if (this.isNew) {
						this.setArticleDetail('category', this.$route.query.category ? this.$route.query.category : data.map(x => x.name)[0])
					}
				}
			}
		},
	},
	methods: {
		setArticleDetail(field, value) {
			if (!this.isNew) {
				let params = {}
				params[field] = value
				this.articleResource.setValue.submit(params)
			} {
				this.updateNewArticleInput({ field, value })
			}
		}
	}
}
</script>