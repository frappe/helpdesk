<template>
	<div
		class="flex h-screen w-screen flex-col items-center justify-center bg-gray-50"
	>
		<div class="mb-8">
			<img
				v-if="configStore.brandLogo"
				:src="configStore.brandLogo"
				class="m-auto h-8"
			/>
			<Logo v-else class="mx-auto h-8" />
		</div>
		<div class="rounded-xl bg-white shadow-xl">
			<div class="w-96 py-8 px-10">
				<div class="mb-6 text-center text-lg">
					{{ title }}
				</div>
				<slot></slot>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { useConfigStore } from "@/stores/config";
import Logo from "~icons/logos/helpdesk";

defineProps({
	title: {
		type: String,
		required: true,
	},
});

const configStore = useConfigStore();
</script>
