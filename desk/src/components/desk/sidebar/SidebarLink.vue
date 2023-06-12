<template>
  <div
    class="flex h-7 cursor-pointer items-center rounded-lg px-1.5 text-gray-700 transition-all duration-300 ease-in-out"
    :class="{
      'w-full': sidebarStore.isExpanded,
      'w-7': !sidebarStore.isExpanded,
      'bg-gray-200': isActive,
      'hover:bg-gray-300': isActive,
      'hover:bg-gray-100': !isActive,
    }"
    @click="handle"
  >
    <component :is="icon" class="h-4 w-4 shrink-0"></component>
    <div
      class="ml-2 shrink-0 text-sm transition-all duration-300 ease-in-out"
      :class="{
        'opacity-100': sidebarStore.isExpanded,
        'opacity-0': !sidebarStore.isExpanded,
        '-z-50': !sidebarStore.isExpanded,
      }"
    >
      {{ label }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useSidebarStore } from "@/stores/sidebar";

const props = defineProps({
  label: {
    type: String,
    required: true,
  },
  icon: {
    type: Object,
    required: true,
  },
  to: {
    type: String,
    required: false,
    default: "",
  },
  onClick: {
    type: Function,
    required: false,
    default: () => true,
  },
});

const route = useRoute();
const router = useRouter();
const sidebarStore = useSidebarStore();
const isActive = computed(() => props.to.includes(route.name.toString()));

function handle() {
  props.onClick();
  if (props.to) {
    router.push({
      name: props.to,
    });
  }
}
</script>
