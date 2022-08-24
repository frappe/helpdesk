<template>
	<Dialog :options="{title: 'New Category'}" :show="open" @close="() => { 
			newCategoryInputErrors = {name: '', parent: '', others: ''}
			open = false
			$emit('close')
		}"
	>
		<template #body-content>
			<div class="flex flex-col space-y-3">
				<div>
					<Input label="Category name" :value="newCategoryName" type="text" @change="(val) => { 
						newCategoryInputValues.name = val 
						newCategoryInputErrors.name = ''
					}" />
					<ErrorMessage :message="newCategoryInputErrors.name" />
				</div>
				<div>
					<Input label="Parent category" type="select" :options="parentCategories" @change="(val) => {
						newCategoryInputValues.parent = val
						newCategoryInputErrors.parent =	''
					}" />
					<ErrorMessage :message="newCategoryInputErrors.parent" />
				</div>
				<ErrorMessage :message="newCategoryInputErrors.others" />
			</div>
		</template>
		<template #actions>
			<div>
				<Button 
					:loading="$resources.createNewCategory.loading"
					appearance="primary" 
					@click="() => {
						if (validateNewCategoryInputs()) {
							$resources.createNewCategory.submit({
								name: newCategoryInputValues.name,
								parent: newCategoryInputValues.parent
							})
						}
					}"
				>
					Add Category
				</Button>
			</div>
		</template>
	</Dialog>
</template>

<script>
import { Dialog, ErrorMessage } from 'frappe-ui';
import { computed, ref } from 'vue'

export default {
	name: 'NewCategoryDialog',
	components: {
		Dialog,
		ErrorMessage
	},
	props: {
		newCategoryName: {
			type: String,
			default: '',
		},
		modelValue: {
			type: Boolean,
			required: true,
		},
		createParentCategories: {
			type: Boolean,
			default: true
		},
	},
	emits: ['update:modelValue', 'close', 'new-category-created'],
	setup(props, { emit }) {
		let open = computed({
			get: () => props.modelValue,
			set: (val) => {
				emit('update:modelValue', val)
				if (!val) {
					emit('close')
				}
			},
		})
		const newCategoryInputValues = ref({name: '', parent: ''})
		const newCategoryInputErrors = ref({name: '', parent: '', others: ''})

		return {
			newCategoryInputValues,
			newCategoryInputErrors,
			open
		}
	},
	computed: {
		parentCategories() {
			if (this.$resources.allParentCategories.data) {
				let categories = []
				if (this.createParentCategories) {
					categories.push('none')
				}
				this.$resources.allParentCategories.data.forEach(category => {
					categories.push(category.name)
				})
				this.newCategoryInputValues.parent = categories[0]
				return categories
			} else {
				return []
			}
		} 
	},
	methods: {
		validateNewCategoryInputs() {
			this.newCategoryInputErrors = {name: '', parent: '', others: ''}

			if (!this.newCategoryInputValues.name) {
				this.newCategoryInputErrors.name = "Category name is required"
			} else if (this.newCategoryInputValues.name.length < 3) {
				this.newCategoryInputErrors.name = "Category name should have atleast 3 characters"
			}

			return !Object.values(this.newCategoryInputErrors).some(val => val)
		}
	},
	resources: {
		allParentCategories() {
			return {
				method: 'frappe.client.get_list',
				params: {
					doctype: 'Category',
					filters: {is_group: ['=', 1]},
					fields: ['name']
				},
				auto: true,
			}
		},
		createNewCategory() {
			return {
				method: 'frappe.client.insert',
				makeParams({ name, parent }) {
					return {
						doc: {
							doctype: 'Category',
							category_name: name,
							parent_category: parent === 'none' ? '' : parent,
							is_group: parent === 'none' ? 1 : 0,
						},
					}
				},
				onSuccess(doc) {
					this.open = false
					this.newCategoryInputValues = {}
					this.$toast({
						title: 'New category created successfully',
						customIcon: 'circle-check',
						appearance: 'success'
					})
					this.$emit('new-category-created', doc.name)
					this.$emit('close', doc.name)
				},
				onError(err) {
					this.newCategoryInputErrors.others = err
					this.$toast({
						title: 'Error while creating category!',
						customIcon: 'circle-fail',
						appearance: 'danger',
					})
				}
			}
		}
	}
}
</script>

<style>

</style>