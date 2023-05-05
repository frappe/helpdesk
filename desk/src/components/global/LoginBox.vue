<template>
	<div class="flex h-screen w-screen items-center justify-center">
		<div class="rounded-xl shadow-xl">
			<img
				v-if="configStore.brandLogo"
				:src="configStore.brandLogo"
				class="m-auto h-6"
			/>
			<div v-else class="flex">
				<div class="mx-auto h-6 w-auto">
					<CustomIcons name="frappedesk" class="h-6" />
				</div>
			</div>
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
import CustomIcons from "@/components/desk/global/CustomIcons.vue";

defineProps({
	title: {
		type: String,
		required: true,
	},
});

const configStore = useConfigStore();
</script>
