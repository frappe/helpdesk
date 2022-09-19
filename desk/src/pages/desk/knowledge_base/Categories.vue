<template>
	<div class="px-[16px]">
		<ListManager
				ref="categories"
				:options="{
					doctype: 'Category',
					fields: ['name', 'description'],
					limit: 100,
					order_by: 'idx desc',
				}"
			>
			<template #body="{ manager }">
				<div class="flex flex-col">
					<div class="h-[72px] py-[22px]">
						<div class="float-right">
							<div class="flex items-center space-x-3">
								<div class="stroke-blue-500 fill-blue-500 w-0 h-0 block"></div>
								<Button icon-left="plus" appearance="primary" @click="newCategoryCreationParams.showDialog = true">Add Category</Button>
							</div>
						</div>
					</div>
					<div v-if="!manager.loading" class="px-5">
						<div class="flex flex-wrap">
							<div v-for="category in manager.list" :key="category.name">
								<router-link 
									:to="`/frappedesk/knowledge-base/${category.name}`" 
									custom v-slot="{ href, navigate }"
								>
									<div
										class="select-none rounded-lg flex flex-col hover:shadow-sm border p-5 mb-4 mx-2 h-[180px] w-[250px] group cursor-pointer"
									>
										<div class="flex flex-row items-center">
											<a :href="href" @click="navigate" class="text-[16px] font-normal mb-3 grow">
												{{ category.name }}
											</a>
											<div class="h-full flex flex-row space-x-3 invisible group-hover:visible">
												<a category_name="Edit">
													<FeatherIcon 
														name="edit-2" 
														class="h-3 w-3 hover:stroke-2 stroke-1"
														@click="() => {
															const _ = editCategoryParams
															_.categoryToEdit = category.name
															_.inputValues = {
																category_name: category.name,
																description: category.description
															}
															_.showDialog = true
															editCategoryParams = _
														}"
													/>
												</a>
												<a category_name="Delete">
													<FeatherIcon 
														name="trash" 
														class="h-3 w-3 stroke-red-400 hover:stroke-2 stroke-1" 
														@click="() => {
															categoryDeletionParams.categoryToDelete = category.name
															categoryDeletionParams.showDialog = true
														}"
													/>
												</a>
											</div>
										</div>
										<a :href="href" @click="navigate" class="text-base h-full">
											{{ category.description }}
										</a>
									</div>
								</router-link>
							</div>
						</div>
					</div>
				</div>
			</template>
		</ListManager>
		<Dialog 
			:options="{
				title: `New Category`, 
				actions: [
					{
						label: 'Create',
						appearance: 'primary',
						handler: () => {
							const _ = newCategoryCreationParams
							if (_.validateInput()) {
								$resources.createNewCategory.submit({
									doc: {
										doctype: 'Category',
										category_name: _.inputValues.category_name,
										description: _.inputValues.description
									}
								})
								_.reset()
							}
						}
					},
					{
						label: 'Cancel',
						appearance: 'secondary',
						handler: () => { 
							newCategoryCreationParams.reset()
						}
					},
				]
			}" 
			:show="newCategoryCreationParams.showDialog"
			@close="newCategoryCreationParams.reset()"
		>
			<template #body-content>
				<div class="flex flex-col space-y-2">
					<div>
						<Input 
							type="text" 
							label="Category Name" 
							@change="(val) => { newCategoryCreationParams.inputValues.category_name = val }" 
						/>
						<ErrorMessage :message="newCategoryCreationParams.validationErrors.category_name" />
					</div>
					<div>
						<Input 
							type="textarea" 
							label="Description" 
							@change="(val) => { newCategoryCreationParams.inputValues.description = val }" 
						/>
						<ErrorMessage :message="newCategoryCreationParams.validationErrors.description" />
					</div>
				</div>
			</template>
		</Dialog>
		<Dialog 
			:options="{
				title: `Edit Category`, 
				actions: [
					{
						label: 'Save',
						appearance: 'primary',
						handler: () => {
							const _ = editCategoryParams
							if (_.validateInput()) {
								$resources.updateCategory.submit({
									old_category_name: _.categoryToEdit,
									new_category_name: _.inputValues.category_name,
									new_description: _.inputValues.description
								})
								_.reset()
							}
						}
					},
					{
						label: 'Cancel',
						appearance: 'secondary',
						handler: () => { 
							editCategoryParams.reset()
						}
					},
				]
			}" 
			:show="editCategoryParams.showDialog"
			@close="editCategoryParams.reset()"
		>
			<template #body-content>
				<div class="flex flex-col space-y-2">
					<div>
						<Input 
							type="text" 
							label="Category Name" 
							:value="editCategoryParams.inputValues.category_name" 
							@change="(val) => { editCategoryParams.inputValues.category_name = val }" 
						/>
						<ErrorMessage :message="editCategoryParams.validationErrors.category_name" />
					</div>
					<div>
						<Input 
							type="textarea" 
							label="Description" 
							:value="editCategoryParams.inputValues.description" 
							@change="(val) => { editCategoryParams.inputValues.description = val }" 
						/>
						<ErrorMessage :message="editCategoryParams.validationErrors.description" />
					</div>
				</div>
			</template>
		</Dialog>
		<Dialog 
			:options="{
				title: `Delete Category`, 
				actions: [
					{
						label: 'Delete',
						appearance: 'danger',
						handler: () => {
							const _ = categoryDeletionParams
							if(_.validateInput()) {
								$resources.deleteCategory.submit({
									category: _.categoryToDelete
								})
								_.reset()
							}
						}
					},
					{
						label: 'Cancel',
						appearance: 'secondary',
						handler: () => {
							categoryDeletionParams.reset()
						}
					},
				]
			}" 
			:show="categoryDeletionParams.showDialog"
			@close="categoryDeletionParams.reset()"
		>
			<template #body-content>
				<div class="flex flex-col space-y-3">
					<div class="text-base font-normal flex flex-col">
						<p>Are you sure you want to delete this category? Please type <span class="font-semibold">{{ categoryDeletionParams.categoryToDelete }}</span> to confirm. </p>
					</div>
					<div>
						<Input 
							type="text"
							@change="(val) => { categoryDeletionParams.inputValue = val }" 
						/>
						<ErrorMessage :message="categoryDeletionParams.validationError" />
					</div>
				</div>
			</template>
		</Dialog>
		</div>
</template>

<script>
import ListManager from '@/components/global/ListManager.vue';
import { FeatherIcon, ErrorMessage } from 'frappe-ui';
import { ref } from 'vue'

export default {
	name: 'Categories',
	components: {
		ListManager,
		FeatherIcon,
		ErrorMessage
	},
	setup() {     
		const newCategoryCreationParams = ref({
			showDialog: false,
			inputValues: {
				category_name: '',
				description: '',
			},
			validationErrors: {
				category_name: '',
				description: '',
			},
			validateInput: () => {
				var _ = newCategoryCreationParams.value
				_.validationErrors = {
					category_name: '',
					description: '',
				}
				if (_.inputValues.category_name === '') {
					_.validationErrors.category_name = 'Category name cannot be empty'
				}
				if (_.inputValues.description.length > 145) {
					_.validationErrors.description = 'Description must should be less than 145 characters'
				}
				newCategoryCreationParams.value = _
				
				return _.validationErrors.category_name === '' && _.validationErrors.description === ''
			},
			reset: () => {
				var _ = newCategoryCreationParams.value
				_.inputValues = {
					category_name: '',
					description: '',
				}
				_.validationErrors = {
					category_name: '',
					description: '',
				}
				_.showDialog = false
				newCategoryCreationParams.value = _
			}
		})

		const editCategoryParams = ref({
			showDialog: false,
			categoryToEdit: '',
			inputValues: {
				category_name: '',
				description: '',
			},
			validationErrors: {
				category_name: '',
				description: '',
			},
			validateInput: () => {
				var _ = editCategoryParams.value
				_.validationErrors = {
					category_name: '',
					description: '',
				}
				if (_.inputValues.category_name === '') {
					_.validationErrors.category_name = 'Category name cannot be empty'
				}
				if (_.inputValues.description === '') {
					_.validationErrors.description = 'Description cannot be empty'
				} else if (_.inputValues.description.length > 145) {
					_.validationErrors.description = 'Description must should be less than 145 characters'
				}
				editCategoryParams.value = _
				
				return _.validationErrors.category_name === '' && _.validationErrors.description === ''
			},
			reset: () => {
				var _ = editCategoryParams.value
				_.inputValues = {
					category_name: '',
					description: '',
				}
				_.validationErrors = {
					category_name: '',
					description: '',
				}
				_.showDialog = false
				editCategoryParams.value = _
			}
		})

		const categoryDeletionParams = ref({
			showDialog: false,
			categoryToDelete: '',
			inputValue: '',
			validationError: '',
			validateInput: () => {
				var _ = categoryDeletionParams.value
				_.validationError = ''
				if (_.inputValue != _.categoryToDelete) {
					_.validationError = 'Please type the category name to confirm.'
				}
				categoryDeletionParams.value = _
				
				return _.validationError === ''
			},
			reset: () => {
				var _ = categoryDeletionParams.value
				_.inputValue = ''
				_.validationError = ''
				_.showDialog = false
				categoryDeletionParams.value = _
			}
		})

		return {
			newCategoryCreationParams,
			editCategoryParams,
			categoryDeletionParams
		}
	},
	resources: {
		createNewCategory() {
			return {
				method: 'frappe.client.insert',
				onSuccess: () => {
					this.$toast({
						title: 'New cateogry created!!',
                        customIcon: 'circle-check',
                        appearance: 'success'
					})
					this.$refs.categories.manager.reload()
				},
				onError: () => {
					this.$toast({
						title: 'Error creating new cateogry!!',
						customIcon: 'circle-fail',
						appearance: 'danger',
					})
				}
			}
		},
		updateCategory() {
			return {
				method: 'frappedesk.api.kb.update_category',
				onSuccess: () => {
					this.$toast({
						title: 'Category updated!!',
						customIcon: 'circle-check',
						appearance: 'success'
					})
					this.$refs.categories.manager.reload()
				},
				onError: () => {
					this.$toast({
						title: 'Error updating category!!',
						customIcon: 'circle-fail',
						appearance: 'danger',
					})
				}
			}
		},
		deleteCategory() {
			return {
				method: 'frappedesk.api.kb.delete_category',
				onSuccess: () => {
					this.$toast({
						title: 'Category deleted!!',
						customIcon: 'circle-check',
						appearance: 'success'
					})
					this.$refs.categories.manager.reload()
				},
				onError: (res) => {
					this.$toast({
						title: 'Category cannot be deleted!!',
						text: res,
						customIcon: 'circle-fail',
						appearance: 'danger',
					})
				}
			}
		}
	}
}
</script>