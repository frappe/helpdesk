<template>
	<div class="grid grid-cols-1 place-content-center">
		<div class="grid place-content-center gap-5 text-center bg-gray-100 w-full h-[250px]">
			<div class="text-[36px] text-gray-700">How can I help you?</div>
			<div class="rounded-xl max-w-3xl shadow bg-white h-10 flex flex-row items-center px-3 space-x-3">
				<FeatherIcon name="search" class="h-4 w-4 stroke-gray-500"/>
				<div class="grow text-[12px] text-left text-gray-500">Write a question or problem</div>
			</div>
		</div>
		<CategoryList 
			:editable="editable" 
			:viewMode="viewMode" 
		/>
	</div>
</template>

<script>
import { FeatherIcon } from 'frappe-ui';
import { ref } from 'vue'
import CategoryList from '@/components/global/CategoryList.vue'

export default {
	name: 'KBHome',
	props: {
		editable: {
			type: Boolean,
			default: false
		}
	},
	components: {
		FeatherIcon,
		CategoryList
	},
	setup() {
		const viewMode = ref('website')

		return {
			viewMode
		}
	}
}
</script>