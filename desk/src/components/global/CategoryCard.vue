<template>
	<div class="bg-white grow shadow rounded p-5 cursor-pointer group flex flex-row space-x-2 h-full">
		<div class="flex flex-row items-center grow">
			<div class="grow flex flex-col space-y-2" :class="editMode ? 'h-[90px]' : ''">
				<div class="flex flex-col">
					<input 
						ref="categoryName"
						type="text" 
						:disabled="!editMode" 
						class="border-none p-0 text-gray-700 text-[14px] focus:ring-0"
						:class="editMode ? '' : 'cursor-pointer'" 
						:value="category.category_name" 
						@input="onCategoryNameInput($event.target.value)"
					/>
					<ErrorMessage :message="validationErrors.category_name"/>
				</div>
				<div class="flex flex-col">
					<textarea 
						ref="categoryDescription"
						rows="2" 
						maxlength="80" 
						:disabled="!editMode"
						class="resize-none border-none p-0 text-[12px] text-gray-600 focus:ring-0"
						:class="editMode ? '' : 'cursor-pointer'" 
						:value="category.description" 
						@input="onDescriptionInput($event.target.value)"
					/>
					<ErrorMessage :message="validationErrors.description"/>
				</div>
			</div>
		</div>
		<div v-if="editMode" class="w-[30px] h-full flex flex-col justify-between items-center opacity-50">
			<div class="flex flex-row-reverse">
				<CustomIcons name="drag-handle" class="w-4 h-4 handle cursor-grab" />
			</div>
			<div class="flex flex-row-reverse" v-if="deletable">
				<Tooltip text="Delete" placement="top">
					<Button icon="trash" appearance="minimal" @click="$emit('delete')"/>
				</Tooltip>
			</div>
		</div>
	</div>
</template>

<script>
import { inject, ref } from 'vue';
import { ErrorMessage, debounce } from 'frappe-ui';
import CustomIcons from '@/components/desk/global/CustomIcons.vue';

export default {
    name: "CategoryCard",
    props: {
        category: {
            type: Object,
            required: true
        },
        editMode: {
            type: Boolean,
            default: false
        },
		deletable: {
			type: Boolean,
			default: false
		}
	},
	components: {
		CustomIcons,
		ErrorMessage
	},
	setup() {
		const validationErrors = ref({
			category_name: "",
			description: ""
		});
		const checkIfCategoryNameExistsInCurrentHierarchy = inject('checkIfCategoryNameExistsInCurrentHierarchy')

		return {
			validationErrors,
			checkIfCategoryNameExistsInCurrentHierarchy
		}
	},
	mounted() {
		if (this.category.is_new) {
			this.focusOnCategoryNameInput()
		}
	},
	watch: {
		editMode(val) {
			if (!val) {
				this.validationErrors = {
					category_name: "",
					description: ""
				}
			}
		}
	},
	resources: {
		checkIfCategoryNameExistsOutsideCurrentHierarchy() {
			return {
				method: 'frappedesk.api.kb.check_if_category_name_exists_outside_current_hierarchy',
				onSuccess: (exists) => {
					if (exists) {
						this.validationErrors.category_name = `${this.category.category_name} already exists.`;
					}
				}
			}
		}
	},
    methods: {
        focusOnCategoryNameInput() {
            this.$nextTick(() => {
                this.$refs.categoryName.focus();
            });
        },
		onCategoryNameInput: debounce(function(value) {
			this.category.category_name = value
			this.validationErrors.category_name = "";
			if (this.checkIfCategoryNameExistsInCurrentHierarchy(value, this.category.idx)) {
				this.$resources.checkIfCategoryNameExistsOutsideCurrentHierarchy.submit({
					category_name: this.category.category_name,
					parent_category: this.category.parent_category
				})
			} else {
				this.validationErrors.category_name = `${this.category.category_name} already exists.`;
			}
		}, 300),
		onDescriptionInput: debounce(function(value) {
			this.category.description = value
			this.validationErrors.description = "";
			// TODO: do validations if required
		}, 300)
    }
}
</script>