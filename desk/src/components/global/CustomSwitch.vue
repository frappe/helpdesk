<template>
	<div :class="disabled ? 'pointer-events-none' : ''">
		<Switch
			v-model="modelValue"
			:class="
				disabled
					? 'border-gray-300'
					: modelValue
					? 'border-blue-500'
					: 'border-gray-700'
			"
			class="relative inline-flex items-center h-4 bg-white border rounded-full w-[1.7rem]"
		>
			<span
				:class="`${
					modelValue ? 'translate-x-[0.9rem]' : 'translate-x-1'
				} ${
					disabled
						? 'bg-gray-300'
						: modelValue
						? 'bg-blue-500'
						: 'bg-gray-700'
				}`"
				class="inline-block w-[0.5rem] h-[0.5rem] transform rounded-full"
			/>
		</Switch>
	</div>
</template>

<script>
import { Switch } from "@headlessui/vue"

export default {
	name: "CustomSwitch",
	components: {
		Switch,
	},
	props: {
		modelValue: {
			type: [Boolean],
		},
		disabled: {
			type: [Boolean],
		},
	},
	watch: {
		modelValue(newValue) {
			this.$emit("update:modelValue", newValue)
		},
	},
}
</script>

<style></style>
