<template>
	<div>
		<button
			@click="toggleAccordion()"
			class="flex items-center space-x-3"
			:aria-expanded="isOpen"
			:aria-controls="`collapse${_uid}`"
		>
			<CustomIcons
				:class="{
					'rotate-180': isOpen,
					'rotate-0': !isOpen,
				}"
				name="chevron-down-accordion"
			/>
			<slot name="title" />
		</button>

		<div v-show="isOpen" :id="`collapse${_uid}`">
			<slot name="content" />
		</div>
	</div>
</template>

<script>
import CustomIcons from "@/components/desk/global/CustomIcons.vue"
export default {
	name: "Accordion",
	components: {
		CustomIcons,
	},
	data() {
		return {
			isOpen: false,
		}
	},
	methods: {
		toggleAccordion() {
			this.isOpen = !this.isOpen
		},
	},
}
</script>
