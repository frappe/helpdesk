<template>
	<div
		class="select-none py-4"
		:class="{
			'border-b': !isExpanded,
		}"
	>
		<div
			class="flex cursor-pointer items-center justify-between"
			@click="isExpanded = !isExpanded"
		>
			<div class="text-base font-medium text-gray-800">Open tickets</div>
			<IconCaretUp v-if="isExpanded" class="h-4 w-4 text-gray-600" />
			<IconCaretDown v-else class="h-4 w-4 text-gray-600" />
		</div>
		<div v-if="isExpanded" class="flex flex-col gap-2 pt-4">
			<div v-for="field in tickets" :key="field.name">
				<a :href="field.url" target="_blank" class="flex items-start gap-2">
					<div class="flex h-5 w-5 items-center justify-center">
						<IconWebLink class="h-5 w-5 text-gray-600" />
					</div>
					<div class="text-base text-gray-800">{{ field.title }}</div>
				</a>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import IconWebLink from "~icons/espresso/web-link";
import IconCaretDown from "~icons/ph/caret-down";
import IconCaretUp from "~icons/ph/caret-up";

const isExpanded = ref(false);
const tickets = [
	{
		name: 1,
		title: "Ticket #1",
		url: "https://example.frappe.cloud/",
	},
	{
		name: 2,
		title: "Ticket #2",
		url: "https://example.frappe.cloud/",
	},
	{
		name: 3,
		title: "Ticket #3",
		url: "https://example.frappe.cloud/",
	},
	{
		name: 4,
		title: "A long ticket name that might be multiple lines long",
		url: "https://example.frappe.cloud/",
	},
];
</script>
