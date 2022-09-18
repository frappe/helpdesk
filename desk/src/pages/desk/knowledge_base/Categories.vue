<template>
	<div class="px-[16px]">
		<ListManager
				ref="categories"
				:options="{
					doctype: 'Category',
					fields: ['name', 'description'],
					limit: 100,
					order_by: 'idx',
				}"
			>
			<template #body="{ manager }">
				<div class="flex flex-col">
					<div class="h-[72px] py-[22px] px-[16px]">
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
								<div class="select-none rounded-lg flex flex-col hover:shadow-sm border p-5 mb-4 mx-2 h-[180px] w-[250px] group cursor-pointer">
									<div class="flex flex-row items-center">
										<div class="text-[16px] font-normal mb-3 grow">
											{{ category.name }}
										</div>
										<div class="h-full flex flex-row space-x-3 invisible group-hover:visible">
											<a title="Edit">
												<FeatherIcon 
													name="edit-2" 
													class="h-3 w-3 hover:stroke-2 stroke-1"
													@click="() => {
														editCategoryParams.inputValues = {
															title: category.name,
															description: category.description
														}
														editCategoryParams.showDialog = true
													}"
												/>
											</a>
											<a title="Delete">
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
									<div class="text-base">
										{{ category.description }}
									</div>
								</div>
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
							if (newCategoryCreationParams.validateInput()) {

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
							label="Title" 
							@change="(val) => { newCategoryCreationParams.inputValues.title = val }" 
						/>
						<ErrorMessage :message="newCategoryCreationParams.validationErrors.title" />
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
							if (editCategoryParams.validateInput()) {

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
							label="Title" 
							:value="editCategoryParams.inputValues.title" 
							@change="(val) => { editCategoryParams.inputValues.title = val }" 
						/>
						<ErrorMessage :message="editCategoryParams.validationErrors.title" />
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
							if(categoryDeletionParams.validateInput()) {

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
				title: '',
				description: '',
			},
			validationErrors: {
				title: '',
				description: '',
			},
			validateInput: () => {
				var _ = newCategoryCreationParams.value
				_.validationErrors = {
					title: '',
					description: '',
				}
				if (_.inputValues.title === '') {
					_.validationErrors.title = 'Title cannot be empty'
				}
				if (_.inputValues.description === '') {
					_.validationErrors.description = 'Description cannot be empty'
				} else if (_.inputValues.description.length > 200) {
					_.validationErrors.description = 'Description must should be less than 200 characters'
				}
				newCategoryCreationParams.value = _
			},
			reset: () => {
				var _ = newCategoryCreationParams.value
				_.inputValues = {
					title: '',
					description: '',
				}
				_.validationErrors = {
					title: '',
					description: '',
				}
				_.showDialog = false
				newCategoryCreationParams.value = _
			}
		})

		const editCategoryParams = ref({
			showDialog: false,
			inputValues: {
				title: '',
				description: '',
			},
			validationErrors: {
				title: '',
				description: '',
			},
			validateInput: () => {
				var _ = editCategoryParams.value
				_.validationErrors = {
					title: '',
					description: '',
				}
				if (_.inputValues.title === '') {
					_.validationErrors.title = 'Title cannot be empty'
				}
				if (_.inputValues.description === '') {
					_.validationErrors.description = 'Description cannot be empty'
				} else if (_.inputValues.description.length > 200) {
					_.validationErrors.description = 'Description must should be less than 200 characters'
				}
				editCategoryParams.value = _
			},
			reset: () => {
				var _ = editCategoryParams.value
				_.inputValues = {
					title: '',
					description: '',
				}
				_.validationErrors = {
					title: '',
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
				} else {
					console.log('delete')
				}
				categoryDeletionParams.value = _
			},
			reset: () => {
				var _ = categoryDeletionParams.value
				_.validateInput = ''
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

			}
		},
		deleteCategory() {
			return {

			}
		}
	}
}
</script>