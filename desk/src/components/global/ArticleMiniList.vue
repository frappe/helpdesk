<template>
	<KBEditableBlock
		:editable="editable"
		:editMode="editMode"
		:saveInProgress="$resources.saveArticles.loading"
		:disableSaving="disableSaving"
		@edit="() => {
			editMode = true
		}"
		@discard="() => {
			editMode = false
		}"
		@save="() => {
			if(validateChanges()) {
				saveChanges()
			}
		}"
	>
		<template #body>
			<draggable 
				:list="articles"
				:disabled="!editMode"
				handle=".handle" 
				item-key="idx"
				class="grid place-content-center grid-cols-2 gap-y-6"
				:class="editMode ? 'gap-x-1 mr-[-1.25rem]' : 'gap-x-6'"
			>
				<template #item="{element}">
					<div class="flex flex-row items-center space-x-1">
						<div class="handle">
							{{ element.title }}
						</div>
					</div>
				</template>
			</draggable>
		</template>
	</KBEditableBlock>
</template>

<script>
import { ref } from 'vue'
import draggable from 'vuedraggable'
import ArticleMiniListItem from '@/components/global/ArticleMiniListItem.vue'
import KBEditableBlock from '@/components/global/KBEditableBlock.vue'

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
		}
	},
	components: {
		draggable,
		ArticleMiniListItem,
		KBEditableBlock
	},
	setup() {
		const editMode = ref(false)
		const tempArticles = ref([])

		return {
			editMode,
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