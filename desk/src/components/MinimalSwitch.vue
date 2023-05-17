<template>
	<Switch
		:class="enabled ? 'bg-gray-900' : 'bg-gray-300'"
		class="relative inline-flex h-[16px] w-[26px] items-center rounded-full"
	>
		<span
			:class="enabled ? 'translate-x-3' : 'translate-x-0.5'"
			class="switch-inner inline-block rounded-full bg-white transition"
		/>
	</Switch>
</template>

<script setup lang="ts">
import { Switch } from "@headlessui/vue";

defineProps({
	enabled: {
		type: Boolean,
		required: true,
	},
});
</script>

<style scoped>
.switch-inner {
	height: 12px;
	width: 12px;
	box-shadow: 0px 3px 3px rgba(0, 0, 0, 0.05);
}
</style>
