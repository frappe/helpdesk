<template>
	<div :class="disabled ? 'pointer-events-none' : ''">
		<Switch
			v-model="isSwitchOn"
			:class="
				disabled
					? 'border-gray-300'
					: modelValue
					? 'border-blue-500'
					: 'border-gray-700'
			"
			class="relative inline-flex h-4 w-[1.7rem] items-center rounded-full border bg-white"
		>
			<span
				:class="`${modelValue ? 'translate-x-[0.9rem]' : 'translate-x-1'} ${
					disabled ? 'bg-gray-300' : modelValue ? 'bg-blue-500' : 'bg-gray-700'
				}`"
				class="inline-block h-[0.5rem] w-[0.5rem] rounded-full"
			/>
		</Switch>
	</div>
</template>

<script>
import { ref } from "vue";
import { Switch } from "@headlessui/vue";

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
	emits: ["update:modelValue"],
	data() {
		return {
			isSwitchOn: ref(false),
		};
	},
	watch: {
		isSwitchOn(val) {
			this.$emit("update:modelValue", val);
		},
	},
	mounted() {
		this.isSwitchOn = this.modelValue;
	},
};
</script>
