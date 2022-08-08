<template>
	<div class="flex flex-col space-y-[16px]">
		<div class="font-semibold text-[24px] prose prose-p:my-1"> {{ title }} </div>
		<div v-html="content"></div>
	</div>
</template>

<script>
export default {
	name: 'ArticleTitleAndContent',
	props: ['title', 'content']
}
</script>