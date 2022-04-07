<template>
	<div class="flex flex-col items-center rounded-md bg-white p-10 text-base">
		<GreenCheckIcon class="h-8 w-8" />
		<h2 class="mt-4 text-lg font-medium text-gray-900">
			{{ title }}
		</h2>
		<p class="mt-1.5 text-center text-base text-gray-700">
			<slot></slot>
		</p>
	</div>
</template>

<script>
export default {
	name: 'SuccessCard',
	props: ['title', 'message']
};
</script>