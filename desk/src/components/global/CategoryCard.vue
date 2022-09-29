<template>
	<div class="bg-white grow shadow rounded p-5 cursor-pointer group flex flex-row space-x-2 h-full">
		<div class="flex flex-row items-center grow">
			<div class="grow flex flex-col space-y-2">
				<input 
					ref="categoryName"
					type="text" 
					:disabled="!editMode" 
					class="border-none p-0 text-gray-700 text-[14px] focus:ring-0"
					:class="editMode ? '' : 'cursor-pointer'" 
					:value="category.category_name" 
					@input="category.category_name = $event.target.value"
				/>
				<textarea 
					ref="categoryDescription"
					rows="2" 
					maxlength="80" 
					:disabled="!editMode"
					class="resize-none border-none p-0 text-[12px] text-gray-600 focus:ring-0"
					:class="editMode ? '' : 'cursor-pointer'" 
					:value="category.description" 
					@input="category.description = $event.target.value"
				/>
			</div>
		</div>
		<div v-if="editMode" class="w-[30px] h-full flex flex-col justify-between items-center opacity-50">
			<div class="flex flex-row-reverse">
				<CustomIcons name="drag-handle" class="w-4 h-4 handle cursor-grab" />
			</div>
			<div class="flex flex-row-reverse" v-if="deletable">
				<Tooltip text="Delete" placement="top">
					<Button icon="trash" appearance="minimal" @click="() => {
						// TODO: delete the category after showing a warning.
						$emit('delete')
					}"/>
				</Tooltip>
			</div>
		</div>
	</div>
</template>

<script>
import { ref } from 'vue';
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
		CustomIcons
	},
	setup(props) {
		const categoryName = ref(props.category.category_name);
		const categoryDescription = ref(props.category.description);

		return {
			categoryName,
			categoryDescription
		}
	},
	mounted() {
		if (this.category.is_new) {
			this.focusOnCategoryNameInput()
		}
	},
    methods: {
        focusOnCategoryNameInput() {
            this.$nextTick(() => {
                this.$refs.categoryName.focus();
            });
        }
    }
}
</script>