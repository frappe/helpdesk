<template>
	<div class="flex flex-col justify-center border-b border-gray-100 px-5 py-3">
		<div class="text-xl font-medium text-gray-900 line-clamp-1">
			{{ title }}
		</div>
		<div class="flex items-center gap-1 text-base text-gray-600">
			<IconHash />
			{{ id }}
			<IconDot />
			Last modified on 24 nov
		</div>
	</div>
</template>

<script setup lang="ts">
import { toRefs } from "vue";
import IconHash from "~icons/espresso/hash";
import IconDot from "~icons/ph/dot-outline-fill";

const props = defineProps({
	id: {
		type: Number,
		default: NaN,
	},
	title: {
		type: String,
		default: "",
	},
});

const { id, title } = toRefs(props);
</script>
