<template>
	<Dialog
		:options="{
			title: `New Category`,
			actions: [
				{
					label: 'Create',
					appearance: 'primary',
					handler: () => {
						if (validateInput()) {
							$resources.createNewCategory.submit({
								doc: {
									doctype: 'Category',
									category_name: inputValues.category_name,
									description: inputValues.description,
								},
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
			<div class="flex flex-col space-y-2">
				<div>
					<Input
						type="text"
						label="Category Name"
						@change="
							(val) => {
								inputValues.category_name = val
							}
						"
					/>
					<ErrorMessage :message="validationErrors.category_name" />
				</div>
				<div>
					<Input
						type="textarea"
						label="Description"
						@change="
							(val) => {
								inputValues.description = val
							}
						"
					/>
					<ErrorMessage :message="validationErrors.description" />
				</div>
			</div>
		</template>
	</Dialog>
</template>

<script>
import { ref } from "vue"

export default {
	name: "NewCategoryDialog",
	props: {
		show: {
			type: Boolean,
			default: false,
		},
	},
	setup(props, context) {
		const inputValues = ref({
			category_name: "",
			description: "",
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
			inputValues,
			validationErrors,
			validateInput,
			reset,
		}
	},
	resources: {
		createNewCategory() {
			return {
				method: "frappe.client.insert",
				onSuccess: (doc) => {
					this.$toast({
						title: "New cateogry created!!",
						customIcon: "circle-check",
						appearance: "success",
					})
					this.$emit("category-created", doc.name)
				},
				onError: () => {
					this.$toast({
						title: "Error creating new cateogry!!",
						customIcon: "circle-fail",
						appearance: "danger",
					})
				},
			}
		},
	},
}
</script>
