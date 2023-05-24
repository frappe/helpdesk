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
		<div class="login-box rounded-xl bg-white">
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

<style scoped>
.login-box {
	box-shadow: rgba(0, 0, 0, 0.16) 0px 10px 36px 0px,
		rgba(0, 0, 0, 0.06) 0px 0px 0px 1px;
}
</style>
