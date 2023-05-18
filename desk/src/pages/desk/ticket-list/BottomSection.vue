<template>
	<div
		v-if="tickets.totalCount"
		class="flex justify-between border-t p-3 text-base"
	>
		<div class="text-gray-600">
			Showing {{ tickets.startFrom }} to {{ tickets.endAt }} of
			{{ tickets.totalCount }}
		</div>
		<div class="flex items-center gap-2 text-gray-600">
			Page
			<div
				class="flex h-5 w-5 flex-wrap content-center justify-center rounded-md bg-gray-200"
			>
				{{ tickets.currentPage }}
			</div>
			of {{ tickets.totalPages }}
			<Button
				v-show="tickets.hasPreviousPage"
				icon="chevron-left"
				class="h-5 w-5 rounded-full bg-gray-200"
				@click="tickets.previous"
			/>
			<Button
				v-show="tickets.hasNextPage"
				icon="chevron-right"
				class="h-5 w-5 rounded-full bg-gray-200"
				@click="tickets.next"
			/>
		</div>
	</div>
</template>

<script setup lang="ts">
import { useTicketListStore } from "./data";

const { tickets } = useTicketListStore();
</script>
