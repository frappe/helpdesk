<template>
	<div
		v-if="ticketList.totalCount"
		class="flex justify-between border-t p-3 text-base"
	>
		<div class="text-gray-600">
			Showing {{ ticketList.startFrom }} to {{ ticketList.endAt }} of
			{{ ticketList.totalCount }}
		</div>
		<div class="flex items-center gap-2 text-gray-600">
			Page
			<div
				class="flex h-5 w-5 flex-wrap content-center justify-center rounded-md bg-gray-200"
			>
				{{ ticketList.currentPage }}
			</div>
			of {{ ticketList.totalPages }}
			<Button
				v-show="ticketList.hasPreviousPage"
				icon="chevron-left"
				class="h-5 w-5 rounded-full bg-gray-200"
				@click="ticketList.previous"
			/>
			<Button
				v-show="ticketList.hasNextPage"
				icon="chevron-right"
				class="h-5 w-5 rounded-full bg-gray-200"
				@click="ticketList.next"
			/>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ticketList } from "./data";
</script>
