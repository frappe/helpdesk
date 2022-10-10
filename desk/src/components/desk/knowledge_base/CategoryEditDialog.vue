<template>
	<Dialog :options="{ title: 'Edit Category' }" v-model="showDialog">
		<template #body-content>
			<div v-if="category" class="flex flex-col">
				<div class="flex flex-col space-y-2">
					<Input
						type="text"
						label="Name"
						:value="category.category_name"
						@input="onCategoryNameInput"
					/>
					<Input
						type="textarea"
						label="Description"
						:value="category.description"
						@input="onCategoryDescriptionInput"
					/>
					<div class="flex flex-col">
						<div class="mb-2 block text-sm leading-4 text-gray-700">
							Path
						</div>
						<div class="flex flex-row space-x-2">
							<div
								class="w-full bg-gray-100 rounded py-1 px-[0.7rem]"
							>
								<Breadcrumbs
									docType="Category"
									:docName="categoryId"
									:interactable="false"
								/>
							</div>
							<Button>Change</Button>
						</div>
					</div>
				</div>
			</div>
		</template>
		<template #actions>
			<Button appearance="primary">Done</Button>
		</template>
	</Dialog>
</template>

<script>
import Breadcrumbs from "@/components/global/kb/Breadcrumbs.vue"
import { debounce } from "frappe-ui"

export default {
	name: "CategoryEditDialog",
	props: {
		categoryId: {
			type: Number,
			default: null,
		},
		isNew: {
			type: Boolean,
			default: false,
		},
		show: {
			type: Boolean,
			default: false,
		},
	},
	components: {
		Breadcrumbs,
	},
	setup() {},
	computed: {
		showDialog: {
			get() {
				return this.show
			},
			set(val) {
				this.$emit("update:show", val)
			},
		},
		category() {
			return this.$resources.category.doc || null
		},
	},
	resources: {
		category() {
			return {
				type: "document",
				doctype: "Category",
				name: this.categoryId,
				auto: true,
			}
		},
		saveChanges() {
			return {
				method: "frappedesk.api.kb.update_category",
				onSuccess: (res) => {
					console.log(res)
				},
				onError: (err) => {
					console.log(err)
				},
			}
		},
	},
	methods: {
		onCategoryNameInput: debounce(function (value) {
			console.log("Category Name Input", value)
		}, 300),
		onCategoryDescriptionInput: debounce(function (value) {
			console.log("Category Description Input", value)
		}, 300),
	},
}
</script>
