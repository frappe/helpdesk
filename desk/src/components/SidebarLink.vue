<template>
  <div
    class="flex h-7 cursor-pointer items-center rounded pl-2 pr-1 text-gray-800 transition-all duration-300 ease-in-out"
    :class="{
      'w-full': isExpanded,
      'w-8': !isExpanded,
      'shadow-sm': isActive,
      'bg-white': isActive,
      'hover:bg-gray-100': !isActive,
    }"
    @click="handle"
  >
    <component :is="icon" class="h-4 w-4 shrink-0 text-gray-700"></component>
    <div
      class="ml-2 flex shrink-0 grow items-center justify-between text-sm transition-all duration-300 ease-in-out"
      :class="{
        'opacity-100': isExpanded,
        'opacity-0': !isExpanded,
        '-z-50': !isExpanded,
      }"
    >
      {{ label }}
      <Tooltip :text="betaText">
        <Badge v-if="isBeta" theme="orange" variant="subtle">beta</Badge>
      </Tooltip>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";
import { Badge, Tooltip } from "frappe-ui";

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
  isExpanded: {
    type: Boolean,
    required: false,
    default: true,
  },
  isActive: {
    type: Boolean,
    required: false,
    default: false,
  },
});

const router = useRouter();
const betaText = "This feature is a work in progress. Use with caution";

function handle() {
  props.onClick();
  if (props.to) {
    router.push({
      name: props.to,
    });
  }
}
</script>
