<template>
  <div
    class="-all flex py-[7px] mx-2 h-7.5 cursor-pointer items-center rounded pl-2 pr-2 text-gray-800 duration-300 ease-in-out"
    :class="{
      'w-auto': isExpanded,
      'w-8': !isExpanded,
      'shadow-sm': isActive,
      [bgColor]: isActive,
      [hvColor]: !isActive,
    }"
    @click="handleNavigation"
  >
    <Tooltip :text="__(label)" v-if="!isExpanded">
      <span
        class="shrink-0 text-gray-700"
        :class="{
          'text-gray-900': !isExpanded,
          'icon-emoji': isMobileView,
        }"
      >
        <component :is="icon" class="h-4 w-4" />
      </span>
    </Tooltip>
    <span
      v-else
      class="shrink-0 text-gray-700"
      :class="{
        'text-gray-900': !isExpanded,
        'icon-emoji': isMobileView,
      }"
    >
      <component :is="icon" class="h-4 w-4" />
    </span>

    <div
      class="-all ml-2 flex min-w-0 items-center justify-between text-sm duration-300 ease-in-out w-full"
      :class="{
        'opacity-100': isExpanded,
        'opacity-0': !isExpanded,
        '-z-50': !isExpanded,
      }"
    >
      <Tooltip :text="__(label)" placement="right">
        <span class="truncate"> {{ __(label) }}</span>
      </Tooltip>
      <slot name="right" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useScreenSize } from "@/composables/screen";
import { useRouter } from "vue-router";

interface P {
  icon?: unknown;
  label: string;
  isExpanded?: boolean;
  isActive?: boolean;
  onClick?: () => void;
  to?: string | object;
  bgColor?: string;
  hvColor?: string;
}

const props = withDefaults(defineProps<P>(), {
  isActive: false,
  onClick: () => () => true,
  to: "",
  bgColor: "bg-white",
  hvColor: "hover:bg-gray-100",
});
const router = useRouter();
const { isMobileView } = useScreenSize();

function handleNavigation() {
  props.onClick();
  if (!props.to) return;
  if (
    props.to === router.currentRoute.value.name &&
    !router.currentRoute.value.query.view
  )
    return;
  if (typeof props.to === "string") {
    router.push({
      name: props.to,
    });
    return;
  }
  router.push(props.to);
}
</script>

<style>
.icon-emoji > div {
  @apply flex items-center justify-center;
}
</style>
