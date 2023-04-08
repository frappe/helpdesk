<template>
	<router-link :to="{ name: to }">
		<div
			class="flex h-8 cursor-pointer items-center rounded-lg px-1.5 text-gray-700 transition-all duration-300 ease-in-out"
			:class="{
				'w-full': sidebarStore.isExpanded,
				'w-8': !sidebarStore.isExpanded,
				'bg-gray-200': isActive,
				'text-gray-900': isActive,
				'hover:bg-gray-300': isActive,
				'hover:bg-gray-100': !isActive,
			}"
		>
			<component
				:is="icon"
				v-show="!isActive"
				class="h-5 w-5 shrink-0"
			></component>
			<component
				:is="iconActive"
				v-show="isActive"
				class="h-5 w-5 shrink-0"
			></component>
			<div
				class="ml-2 shrink-0 transition-all duration-300 ease-in-out"
				:class="{
					'opacity-100': sidebarStore.isExpanded,
					'opacity-0': !sidebarStore.isExpanded,
					'-z-50': !sidebarStore.isExpanded,
				}"
			>
				{{ label }}
			</div>
		</div>
	</router-link>
</template>

<script setup lang="ts">
import { computed, toRefs } from "vue";
import { useRoute } from "vue-router";
import { useSidebarStore } from "@/stores/sidebar";

const props = defineProps({
	label: {
		type: String,
		required: true,
	},
	to: {
		type: String,
		required: true,
	},
	icon: {
		type: Object,
		required: true,
	},
	iconActive: {
		type: Object,
		required: false,
		default: null,
	},
});

const { to } = toRefs(props);
const route = useRoute();
const sidebarStore = useSidebarStore();
const isActive = computed(() => to.value.includes(route.name.toString()));
</script>
