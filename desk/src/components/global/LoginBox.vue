<template>
	<div class="flex h-screen w-screen items-center justify-center">
		<div class="rounded-xl shadow-xl">
			<img
				v-if="configStore.brandLogo"
				:src="configStore.brandLogo"
				class="m-auto h-6"
			/>
			<Logo v-else class="mx-auto h-8" />
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
