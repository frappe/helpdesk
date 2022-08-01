<template>
	<div class="block select-none rounded-[6px] py-[7px] pl-[11px] pr-[9px]" :class="selected ? 'bg-blue-50 hover:bg-blue-100' : 'hover:bg-gray-50'">
		<div 
			v-if="article"
			class="group flex items-center text-base"
		>
			<div 
				class="w-[37px] h-[14px] flex items-center"
			>
				<Input
					type="checkbox" 
					@click="$emit('toggleSelect')" 
					:checked="selected" 
					class="cursor-pointer"
				/>
			</div>
			<div class="sm:w-6/12">
				<router-link 
					:to="`/frappedesk/articles/${article.name}`"
					class="flex items-center space-x-[8px]"
				>
					<div 
						class="truncate max-w-fit lg:w-80 md:w-52 sm:w-40"
					>
						{{ article.title }}
					</div>
					<!-- <div v-if="article.article_type" class="text-gray-600 font-medium bg-gray-200 px-[8px] py-[2px] rounded-[48px] uppercase text-xs">{{ article.article_type }}</div> -->
				</router-link>
			</div>
			<div class="sm:w-3/12">
				<div class="w-full">
					<div class="flex flex-row items-center space-x-1">
						<div class="text-base font-normal">{{ article.author_name }}</div>
					</div>
				</div>
			</div>
			<div class="sm:w-1/12">
				<div class="text-gray-600 font-normal" v-if="article.views">{{ article.views }}</div>
			</div>
			<div class="sm:w-2/12 font-normal">
				<div class="text-gray-600 font-normal text-right" v-if="article.modified">{{ $dayjs(article.modified).format('D MMMM, YYYY') }}</div>
			</div>
		</div>
		<div class="transform translate-y-2"/>
	</div>
</template>

<script>
import CustomIcons from '@/components/desk/global/CustomIcons.vue'
import { ref } from 'vue'

export default {
	name: 'ArticleListItem',
	props: ['article', 'selected'],
	components: {
		CustomIcons
	}
}
</script>
