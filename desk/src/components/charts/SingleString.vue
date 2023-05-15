<template>
	<div class="flex h-full flex-col">
		<div class="select-none pt-1 pl-1 text-base font-medium text-gray-800">
			{{ title }}
		</div>
		<div
			class="flex grow select-none items-center justify-center text-6xl text-gray-800"
		>
			{{ value }}
		</div>
	</div>
</template>

<script setup lang="ts">
defineProps({
	title: {
		type: String,
		required: true,
	},
	value: {
		type: String,
		required: true,
	},
});
</script>
