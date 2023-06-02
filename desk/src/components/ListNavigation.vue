<template>
	<div v-if="totalCount" class="flex justify-between border-t text-base">
		<div class="text-gray-600">
			Showing {{ startFrom }} to {{ endAt }} of
			{{ totalCount }}
		</div>
		<div class="flex items-center gap-2 text-gray-600">
			Page
			<div
				class="flex h-5 w-5 flex-wrap content-center justify-center rounded-md bg-gray-200"
			>
				{{ currentPage }}
			</div>
			of {{ totalPages }}
			<Button
				v-show="hasPreviousPage"
				icon="chevron-left"
				class="h-5 w-5 rounded-full bg-gray-200"
				@click="previous"
			/>
			<Button
				v-show="hasNextPage"
				icon="chevron-right"
				class="h-5 w-5 rounded-full bg-gray-200"
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
