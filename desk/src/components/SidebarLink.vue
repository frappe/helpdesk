<template>
  <div
    class="flex h-7 cursor-pointer items-center rounded pl-2 pr-1 text-gray-800 -all duration-300 ease-in-out"
    :class="{
      'w-full': isExpanded,
      'w-8': !isExpanded,
      'shadow-sm': isActive,
      'bg-white': isActive,
      'hover:bg-gray-100': !isActive,
    }"
    @click="handle"
  >
    <Icon :icon="icon" class="h-4 w-4 shrink-0 text-gray-700"></Icon>
    <div
      class="ml-2 flex shrink-0 grow items-center justify-between text-sm -all duration-300 ease-in-out"
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
import { Icon } from "@iconify/vue";

interface P {
  icon: string;
  label: string;
  isExpanded: boolean;
  isActive?: boolean;
  isBeta?: boolean;
  onClick?: () => void;
  to?: string;
}

const props = withDefaults(defineProps<P>(), {
  isActive: false,
  isBeta: false,
  onClick: () => () => true,
  to: "",
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
