<template>
	<div
		v-if="!manager.loading"
		class="flex w-full justify-between space-x-2 items-center text-gray-600 text-base select-none"
	>
		<div>
			Showing
			<span class="text-gray-900 font-medium">{{ showing.from }}</span>
			-
			<span class="text-gray-900 font-medium">{{ showing.to }}</span>
			of
			<span class="text-gray-900 font-medium">{{ showing.of }}</span>
		</div>
		<div
			class="flex flex-row space-x-0 items-center"
			v-if="manager.totalPages != 1"
		>
			<FeatherIcon
				name="chevron-left"
				@click="
					() => {
						if (manager.hasPreviousPage) {
							manager.previousPage()
						}
					}
				"
				class="rounded-[14px] p-1.5 w-[28px] bg-gray-100 hover:bg-gray-300 stroke-gray-700"
				role="button"
			/>
			<div v-for="i in manager.totalPages" :key="i">
				<div
					v-if="
						[
							1,
							manager.currentPageNumber - 1,
							manager.currentPageNumber,
							manager.currentPageNumber + 1,
							manager.totalPages,
						].includes(i)
					"
					role="button"
					class="rounded-[14px] py-1 w-[28px] text-center mx-1 hover:bg-gray-600 hover:border hover:border-gray-700 hover:text-white"
					:class="{
						'text-white bg-gray-600':
							i === manager.currentPageNumber,
						'text-gray-600': i !== manager.currentPageNumber,
					}"
					@click="
						() => {
							if (manager.currentPageNumber != i) {
								manager.getPage(i)
							}
						}
					"
				>
					{{ i }}
				</div>
				<div
					v-else-if="
						[
							manager.currentPageNumber - 2,
							manager.currentPageNumber + 2,
						].includes(i) &&
						i > 1 &&
						i < manager.totalPages
					"
					class="rounded-[14px] py-1 w-[28px] text-center mx-1"
				>
					...
				</div>
			</div>
			<FeatherIcon
				@click="
					() => {
						if (manager.hasNextPage) {
							manager.nextPage()
						}
					}
				"
				name="chevron-right"
				class="rounded-[14px] p-1.5 w-[28px] bg-gray-100 hover:bg-gray-300 stroke-gray-700"
				role="button"
			/>
		</div>
	</div>
</template>

<script>
import { FeatherIcon } from "frappe-ui"
import { inject, computed, ref } from "vue"

export default {
	name: "ListPageController",
	setup() {
		const manager = inject("manager")
		const from = computed(() => {
			return manager.value.options.start
		})
		const to = computed(() => {
			const start = manager.value.options.start
			const limit = manager.value.options.limit
			if (start + limit > manager.value.totalCount) {
				return manager.value.totalCount
			}
			return start + limit
		})
		const of = computed(() => {
			return manager.value.totalCount
		})
		const showing = ref({
			from,
			to,
			of,
		})
		return {
			manager,
			showing,
		}
	},
	components: { FeatherIcon },
}
</script>
