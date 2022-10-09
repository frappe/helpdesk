<template>
	<div
		class="bg-gray-100 w-full flex items-center"
		:class="isRoot ? 'h-[350px]' : 'h-[236px]'"
	>
		<div class="container flex flex-col space-y-5 mx-auto">
			<div
				class="text-gray-900 font-semibold"
				:class="isRoot ? 'text-[52px]' : 'text-[36px]'"
			>
				{{ isRoot ? "How can I help you?" : "Knowledge Base" }}
			</div>
			<div
				class="rounded-xl max-w-xl shadow bg-white h-10 flex flex-row items-center px-3 space-x-3"
			>
				<FeatherIcon name="search" class="h-4 w-4 stroke-gray-500" />
				<div class="grow text-[12px] text-left text-gray-500">
					Write a question or problem
				</div>
			</div>
		</div>
	</div>
</template>

<script>
export default {
	name: "KBSearchSection",
	props: {
		isRoot: {
			type: Boolean,
			default: false,
		},
	},
}
</script>
