<template>
	<div
		class="flex items-center gap-1 rounded-lg border border-gray-200 px-2.5 py-2 hover:bg-gray-50"
	>
		<div class="flex flex-row items-center space-x-1">
			<component :is="icon" class="h-4 w-4 text-gray-800" />
			<span class="text-sm text-gray-800">
				{{ label }}
			</span>
		</div>
		<slot name="extra"></slot>
	</div>
</template>

<script setup lang="ts">
import { toRefs } from "vue";
import IconFile from "~icons/espresso/file";
import IconPdf from "~icons/espresso/pdf";

const props = defineProps({
	label: {
		type: String,
		required: true,
	},
});

const { label } = toRefs(props);

const icon = label.value.endsWith(".pdf") ? IconPdf : IconFile;
</script>
