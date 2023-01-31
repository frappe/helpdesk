<template>
	<div class="mx-5">
		<button
			@click="
				() => {
					$emit('toggle')
				}
			"
			class="flex flex-row py-2 px-4 bg-gray-50 rounded text-left items-center"
			:aria-expanded="this.isOpen"
			:aria-controls="`collapse${_uid}`"
		>
			<slot name="title" />
			<CustomIcons
				class="float-right"
				:class="{ 'rotate-180': isOpen }"
				name="chevron-down-accordion"
			/>
		</button>
		<div v-show="isOpen" :id="`collapse${_uid}`" class="px-2">
			<slot name="data" />
		</div>
	</div>
</template>

<script>
import CustomIcons from "@/components/desk/global/CustomIcons.vue"
export default {
	name: "Accordion",
	props: {
		isOpen: {
			type: Boolean,
			default: false,
			required: true,
		},
	},
	components: {
		CustomIcons,
	},
}
</script>
