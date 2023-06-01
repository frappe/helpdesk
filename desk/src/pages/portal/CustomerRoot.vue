<template>
	<div class="min-h-screen bg-gray-100">
		<div
			class="mx-auto py-8"
			:style="{
				width: '900px',
			}"
		>
			<div class="mb-8 flex items-center justify-between text-base">
				<span>
					<img
						v-if="configStore.brandLogo"
						:src="configStore.brandLogo"
						class="h-8"
					/>
					<div v-else class="text-6xl text-gray-800">
						{{ configStore.helpdeskName }}
					</div>
				</span>
				<RouterLink :to="{ name: KB_PUBLIC }">
					<div class="flex items-center gap-2">
						<IconKnowledgebase class="h-4 w-4" />
						Knowledge Base &rightarrow;
					</div>
				</RouterLink>
			</div>
			<div
				class="rounded-lg bg-white py-2"
				:style="{
					'box-shadow':
						'0px 0px 1px rgba(0, 0, 0, 0.45), 0px 1px 2px rgba(0, 0, 0, 0.1)',
				}"
			>
				<RouterView />
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { useConfigStore } from "@/stores/config";
import { KB_PUBLIC } from "@/router";
import IconKnowledgebase from "~icons/espresso/knowledge-base";

const configStore = useConfigStore();
</script>
