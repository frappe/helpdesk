<template>
	<div v-if="!manager.loading" class="flex">
		<div v-if="manager.hasNextPage" class="flex flex-row space-x-2">
			<Button @click="manager.nextPage()">Load More</Button>
		</div>
	</div>
</template>

<script>
export default {
	name: "ListPageController",
	inject: ["manager"],
}
</script>
