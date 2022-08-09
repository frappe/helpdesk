<template>
	<div class="flex flex-col">
		<TopNavbar class="h-[52px] border-b" />
		<router-view class="grow" />
	</div>
</template>

<script>
import TopNavbar from '@/components/desk/knowledge_base/TopNavbar.vue'

export default {
	name: 'KnowledgeBase',
	components: {
		TopNavbar,
	}
}
</script>