<template>
	<div 
		class="flex flex-col" 
		:class="editMode ? 'border-2 border-gray-300 rounded p-5 space-y-4 mt-5' : ''"
	>
		<div class="h-12">
			<div v-if="editMode" class="flex flex-row-reverse">
				<Button 
					:loading="$resources.saveCategories.loading"
					icon-left="save" 
					class="ml-2"
					:class="disableSaving ? 'cursor-not-allowed' : ''"
					:disable="disableSaving"
					@click="() => {
						if(validateChanges()) {
							// TODO: save the changes	
							saveChanges()
						}
					}"
				>
					Save
				</Button>
				<Button 
					icon-left="rotate-ccw" 
					@click="() => {
						editMode = false
						// TODO: discard the changes
					}"
				>
					Discard
				</Button>
			</div>
			<div v-else-if="editable" class="flex flex-row-reverse py-2">
				<Button 
					icon-left="edit-2" 
					@click="() => {
						editMode = true
					}"
				>
					Edit
				</Button>
			</div>
		</div>
		<draggable 
			:list="categories"
			:disabled="!editMode"
			handle=".handle" 
			item-key="idx"
			class="grid place-content-center grid-cols-3 gap-y-6"
			:class="editMode ? 'gap-x-1 mr-[-1.25rem]' : 'gap-x-6'"
		>
			<template #item="{element}">
				<div class="flex flex-row items-center space-x-1">
					<CategoryCard 
						class="grow"
						:category="element"
						:editMode="editMode"
						:deletable="categories.length > 1"
						@delete="() => {
							const index = categories.findIndex(c => c == element)
							categories.splice(index, 1)
						}"
						@click="() => {
							if (editMode) return
							$router.push({path: `/frappedesk/knowledge-base/${element.name}`})
						}"
					/>
					<div v-if="editMode" class="group h-full">
						<div class="group-hover:visible invisible flex h-full">
							<FeatherIcon 
								name="plus" 
								class="w-4 cursor-pointer my-auto hover:bg-gray-100 rounded"
								@click="() => {
									const index = categories.findIndex(c => c == element)
									categories.splice(index + 1, 0, {
										is_new: true,
										idx: categories.length,
										category_name: '',
										description: '',
										parent_category: categoryId ? categoryId : null,
										is_group: (!parentCategoryId && !categoryId) ? 1 : 0,	// mark is_group as true if in root, other cases will be decided when child categories are added / removed from the category
									})
								}"
							/>
						</div>
					</div>
				</div>
			</template>
		</draggable>
	</div>
</template>

<script>
import { provide, ref } from 'vue'
import draggable from 'vuedraggable'
import { FeatherIcon } from 'frappe-ui'
import CategoryCard from '@/components/global/CategoryCard.vue'

export default {
	name: 'CategoryCardList',
	props: {
		categoryId: {
			type: String,
			default: null
		},
		parentCategoryId: {
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
		CategoryCard,
		FeatherIcon
	},
	setup() {
		const editMode = ref(false)
		const tempCategories = ref([])
		const allValidationErrors = ref([])

		provide('allValidationErrors', allValidationErrors)

		provide('checkIfCategoryNameExistsInCurrentHierarchy', (categoryName, idx) => {
			return !tempCategories.value.some(c => c.category_name == categoryName && c.idx != idx)
		})
		
		return {
			editMode,

			tempCategories,
			allValidationErrors
		}
	},
	computed: {
		categories() {
			if (!this.editMode) {
				return this.$resources.categories.data || []
			} else {
				return this.tempCategories
			}
		},
		disableSaving() {
			return this.allValidationErrors.length > 0
		}
	},
	watch: {
		editMode(newVal) {
			if (newVal) {
				this.tempCategories = JSON.parse(JSON.stringify(this.$resources.categories.data))
			}
		}
	},
	resources: {
		categories() {
			const filters = this.categoryId ? {'parent_category': this.categoryId} : {'is_group': true, 'parent_category': ''}
			
			return {
				type: 'list',
				cache: ['Categories', this.categoryId ? this.categoryId : ''],
				doctype: 'Category',
				filters,
				fields: [
					'name',
					'category_name', 
					'description', 
					'parent_category', 
					'is_group',
					'idx'
				],
				limit: 999,
				order_by: 'idx',
				realtime: true
			}
		},
		saveCategories() {
			return {
				method: 'frappedesk.api.kb.insert_new_update_existing_categories',
				onSuccess: () => {
					this.editMode = false
					this.$resources.categories.reload()

					this.$toast({
						title: 'Categories updated!!',
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
		}
	},
	methods: {
		validateChanges() {
			return this.allValidationErrors.length == 0
		},
		saveChanges() {
			this.$resources.saveCategories.submit({
				new_values: this.tempCategories,
				old_values: this.$resources.categories.data
			})
		}
	}
}
</script>