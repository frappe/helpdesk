<template>
	<div class="grid grid-cols-1 place-content-center">
		<div class="grid place-content-center gap-5 text-center bg-gray-100 w-full h-[250px]">
			<div class="text-[36px] text-gray-900 font-semibold">How can I help you?</div>
			<div class="rounded-xl max-w-3xl shadow bg-white h-10 flex flex-row items-center px-3 space-x-3">
				<FeatherIcon name="search" class="h-4 w-4 stroke-gray-500"/>
				<div class="grow text-[12px] text-left text-gray-500">Write a question or problem</div>
			</div>
		</div>
		<CategoryCardList
			v-if="!(categoryId && parentCategoryId)"
			:editable="editable" 
			:categoryId="categoryId" 
			:parentCategoryId="parentCategoryId" 
		/>
		<ArticleMiniList 
			v-if="categoryId" 
			:editable="editable" 
			:categoryId="categoryId" 
		/>
		<!-- <FAQList :editable="editable" v-else>
			TODO: Show FAQ edit list
		</FAQList> -->
	</div>
</template>

<script>
import { FeatherIcon } from 'frappe-ui';
import { inject } from 'vue'
import CategoryCardList from '@/components/global/CategoryCardList.vue'
import ArticleMiniList from '@/components/global/ArticleMiniList.vue'

export default {
	name: 'KBHome',
	props: {
		editable: {
			type: Boolean,
			default: false
		},
	},
	components: {
		FeatherIcon,
		CategoryCardList,
		ArticleMiniList
	},
	setup() {
		const categoryId = inject('categoryId')
		const parentCategoryId = inject('parentCategoryId')

		return {
			categoryId,
			parentCategoryId
		}
	}
}
</script>