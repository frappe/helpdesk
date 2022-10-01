<template>
	<div class="flex flex-col space-y-5">
		<div class="text-3xl font-bold text-gray-800">Articles</div>
		<draggable 
			:list="articles"
			:disabled="!editMode"
			item-key="idx"
			class="grow grid place-content-center gap-y-3"
			:class="articles.length > 6 ? 'grid-cols-2' : 'grid-cols-1'"
		>
			<template #item="{element}">
				<div class="flex flex-row items-center space-x-1">
					<ArticleMiniListItem 
						:editMode="editMode" 
						:article="element" 
					/>
				</div>
			</template>
		</draggable>
	</div>
</template>

<script>
import { ref } from 'vue'
import draggable from 'vuedraggable'
import ArticleMiniListItem from '@/components/global/ArticleMiniListItem.vue'

export default {
	name: 'ArticleMiniList',
	props: {
		categoryId: {
			type: String,
			default: null
		},
		editable: {
			type: Boolean,
			default: false
		},
		editMode: {
			type: Boolean,
			default: false
		}
	},
	components: {
		draggable,
		ArticleMiniListItem
	},
	setup() {
		const tempArticles = ref([])

		return {
			tempArticles
		}
	},
	computed: {
		articles() {
			if (!this.editMode) {
				return this.$resources.articles.data || []
			} else {
				return this.tempArticles
			}
		},
		disableSaving() {
			return false // TODO: Add validation
		}
	},
	watch: {
		editMode(newVal) {
			if (newVal) {
				this.tempArticles = JSON.parse(JSON.stringify(this.$resources.articles.data))
			}
		}
	},
	resources: {
		articles() {
			const filters = { category: this.categoryId, published: true }

			return {
				type: 'list',
				cache: ['Articles', this.categoryId, 'published'],
				doctype: 'Article',
				filters,
				fields: [
					'name',
					'title',
					'idx'
				],
				limit: 999,
				order_by: 'idx',
				// realtime: true TODO: if there are any updates inform the user via some promt (also handle editMode: true senarios)
				// or implement colaborative editing
			}
		},
		saveArticles() {
			return {
				method: 'frappedesk.api.kb.update_articles_order_and_status',
				onSuccess: () => {
					this.editMode = false
					this.$resources.articles.reload()

					this.$toast({
						title: 'Articles updated!!',
						customIcon: 'circle-check',
						appearance: 'success',
					})
				},
				onError: (err) => {
					this.$toast({
						title: 'Error while saving',
						text: err,
						customIcon: 'circle-fail',
						appearance: 'danger',
					})
				}
			}
		},
	},
	methods: {
		validateChanges() {
			return true // TODO: implement validation
		},
		saveChanges() {
			this.$resources.saveArticles.submit({
				new_values: this.tempArticles,
				old_values: this.$resources.articles.data
			})
		}
	}
}
</script>