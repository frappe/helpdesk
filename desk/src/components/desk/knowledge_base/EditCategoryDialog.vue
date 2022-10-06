<template>
	<Dialog
		:options="{
			title: `Edit Category`,
			actions: [
				{
					label: 'Save',
					appearance: 'primary',
					handler: () => {
						if (validateInput()) {
							$resources.updateCategory.submit({
								old_category_name: categoryToEdit.category_name,
								new_category_name: inputValues.category_name,
								new_description: inputValues.description,
							})
							reset()
						}
					},
				},
				{
					label: 'Cancel',
					appearance: 'secondary',
					handler: () => {
						reset()
					},
				},
			],
		}"
		:show="show"
		@close="reset()"
	>
		<template #body-content>
			<div>
				<div class="flex flex-col space-y-4 mb-5">
					<div>
						<Input
							type="text"
							label="Category Name"
							:value="inputValues.category_name"
							@change="
								(val) => {
									inputValues.category_name = val
								}
							"
						/>
						<ErrorMessage
							:message="validationErrors.category_name"
						/>
					</div>
					<div>
						<Input
							type="textarea"
							label="Description"
							:value="inputValues.description"
							@change="
								(val) => {
									inputValues.description = val
								}
							"
						/>
						<ErrorMessage :message="validationErrors.description" />
					</div>
				</div>
				<div v-if="showCategoryDeleteAction">
					<div
						v-if="triggerDeleteWarning"
						class="flex flex-row items-center space-x-3"
					>
						<div class="flex flex-col space-y-1 grow">
							<div class="text-[14px]">Delete Category</div>
							<p class="text-[12px] text-gray-700">
								Are you sure you want to delete this category ?
							</p>
						</div>
						<div class="flex flex-row space-x-2">
							<Button
								appearance="secondary"
								@click="
									() => {
										triggerDeleteWarning = false
									}
								"
								>Cancel</Button
							>
							<Button
								appearance="danger"
								@click="
									() => {
										$resources.deleteCategory.submit({
											category:
												categoryToEdit.category_name,
										})
										reset()
									}
								"
							>
								Confirm
							</Button>
						</div>
					</div>
					<div v-else class="flex flex-row items-center space-x-3">
						<div class="flex flex-col space-y-1 grow">
							<div class="text-[14px]">Delete Category</div>
							<p class="text-[12px] text-gray-700">
								Permanently delete this category
							</p>
						</div>
						<div>
							<Button
								appearance="secondary"
								@click="
									() => {
										triggerDeleteWarning = true
									}
								"
								>Delete</Button
							>
						</div>
					</div>
				</div>
			</div>
		</template>
	</Dialog>
</template>

<script>
import { ref } from "@vue/reactivity"
import { ErrorMessage } from "frappe-ui"

export default {
	name: "EditCategoryDialog",
	props: {
		categoryToEdit: {
			type: Object,
			required: true,
		},
		show: {
			type: Boolean,
			required: true,
		},
	},
	components: {
		ErrorMessage,
	},
	watch: {
		show(val) {
			if (val) {
				this.inputValues.category_name =
					this.categoryToEdit.category_name
				this.inputValues.description = this.categoryToEdit.description
			}
		},
	},
	computed: {
		showCategoryDeleteAction() {
			if (
				this.$resources.articleCount.loading ||
				this.$resources.categoryCount.loading
			) {
				return false
			}
			return (
				this.$resources.articleCount.data == 0 &&
				this.$resources.categoryCount.data > 1
			)
		},
	},
	setup(props, context) {
		const triggerDeleteWarning = ref(false)

		const inputValues = ref({
			category_name: props.categoryToEdit.category_name,
			description: props.categoryToEdit.description,
		})
		const validationErrors = ref({
			category_name: "",
			description: "",
		})
		const validateInput = () => {
			validationErrors.value = {
				category_name: "",
				description: "",
			}
			if (inputValues.value.category_name === "") {
				validationErrors.value.category_name =
					"Category name cannot be empty"
			}
			if (inputValues.value.description.length > 145) {
				validationErrors.value.description =
					"Description must should be less than 145 characters"
			}
			return (
				validationErrors.value.category_name === "" &&
				validationErrors.value.description === ""
			)
		}
		const reset = () => {
			inputValues.value = {
				category_name: "",
				description: "",
			}
			validationErrors.value = {
				category_name: "",
				description: "",
			}
			context.emit("close")
		}
		return {
			triggerDeleteWarning,
			inputValues,
			validationErrors,
			validateInput,
			reset,
		}
	},
	resources: {
		updateCategory() {
			return {
				method: "frappedesk.api.kb.update_category",
				onSuccess: () => {
					this.$toast({
						title: "Category updated!!",
						customIcon: "circle-check",
						appearance: "success",
					})
					this.$emit("updated")
				},
				onError: () => {
					this.$toast({
						title: "Error updating category!!",
						customIcon: "circle-fail",
						appearance: "danger",
					})
				},
			}
		},
		deleteCategory() {
			return {
				method: "frappedesk.api.kb.delete_category",
				onSuccess: () => {
					this.$toast({
						title: "Category deleted!!",
						customIcon: "circle-check",
						appearance: "success",
					})
					this.$emit("deleted")
				},
				onError: (res) => {
					this.$toast({
						title: "Category cannot be deleted!!",
						text: res,
						customIcon: "circle-fail",
						appearance: "danger",
					})
				},
			}
		},
		articleCount() {
			return {
				method: "frappe.client.get_count",
				params: {
					doctype: "Article",
					filters: {
						category: this.categoryToEdit.category_name,
					},
				},
				auto: true,
			}
		},
		categoryCount() {
			return {
				method: "frappe.client.get_count",
				params: {
					doctype: "Category",
				},
				auto: true,
			}
		},
	},
}
</script>
