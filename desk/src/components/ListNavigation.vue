<template>
	<div v-if="totalCount" class="border-t text-base">
		<div class="flex items-center justify-end gap-2 text-gray-600">
			<div class="text-gray-600">
				{{ startFrom }}
				-
				{{ endAt }}
				of
				{{ totalCount }}
			</div>
			<Button
				icon="chevron-left"
				class="h-5 w-5 rounded-full"
				:disabled="!hasPreviousPage"
				@click="previous"
			/>
			<Button
				icon="chevron-right"
				class="h-5 w-5 rounded-full"
				:disabled="!hasNextPage"
				@click="next"
			/>
		</div>
	</div>
</template>

<script setup lang="ts">
defineProps({
	startFrom: {
		type: Number,
		required: true,
	},
	endAt: {
		type: Number,
		required: true,
	},
	currentPage: {
		type: Number,
		required: true,
	},
	totalPages: {
		type: Number,
		required: true,
	},
	totalCount: {
		type: Number,
		required: true,
	},
	hasPreviousPage: {
		type: Boolean,
		required: true,
	},
	hasNextPage: {
		type: Boolean,
		required: true,
	},
	next: {
		type: Function,
		required: true,
	},
	previous: {
		type: Function,
		required: true,
	},
});
</script>
