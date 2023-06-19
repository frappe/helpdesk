<template>
  <div
    class="flex h-7 cursor-pointer items-center justify-between rounded-lg px-1.5 text-gray-700 transition-all duration-300 ease-in-out"
    :class="{
      'w-full': sidebarStore.isExpanded,
      'w-7': !sidebarStore.isExpanded,
      'bg-gray-200': isActive,
      'hover:bg-gray-300': isActive,
      'hover:bg-gray-100': !isActive,
    }"
    @click="handle"
  >
    <div class="flex items-center">
      <component :is="icon" class="h-4 w-4 shrink-0"></component>
      <div
        class="ml-2 shrink-0 text-base transition-all duration-300 ease-in-out"
        :class="{
          'opacity-100': sidebarStore.isExpanded,
          'opacity-0': !sidebarStore.isExpanded,
          '-z-50': !sidebarStore.isExpanded,
        }"
      >
        {{ label }}
      </div>
    </div>
    <Badge v-if="isBeta" theme="blue" variant="subtle">beta</Badge>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { Badge } from "frappe-ui";
import { useRoute, useRouter } from "vue-router";
import { useSidebarStore } from "@/stores/sidebar";

const props = defineProps({
  icon: {
    type: Object,
    required: true,
  },
  label: {
    type: String,
    required: true,
  },
  isBeta: {
    type: Boolean,
    required: false,
    default: false,
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
