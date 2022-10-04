<template>
	<div class="flex flex-row border-b border-[#F4F5F6] text-base font-normal">
		<div v-for="option in options" :key="option.name" class="grow">
			<div
				role="button"
				@click="option.action()"
				class="text-center py-[12px] mb-[-1px]"
				:class="
					option.selected
						? 'border-b border-blue-500 text-gray-900'
						: 'text-gray-600'
				"
			>
				{{ option.label }}
			</div>
		</div>
	</div>
</template>

<script>
import { ref } from "@vue/reactivity"
export default {
	name: "AgentRelatedInfoTopPanel",
	setup() {
		const options = ref([])
		return { options }
	},
	mounted() {
		this.options = [
			{
				label: "Tickets",
				name: "tickets",
				action: () => {
					this.changeSection("tickets")
				},
				selected: true,
			},
			{
				label: "Knowledge Base",
				name: "kb",
				action: () => {
					this.changeSection("kb")
				},
			},
		]
	},
	methods: {
		changeSection(section) {
			this.options.forEach((option) => {
				option.selected = option.name === section
			})
			this.$event.emit(
				"agent-related-info-top-panel-selection-change",
				section
			)
		},
	},
}
</script>

<style></style>
