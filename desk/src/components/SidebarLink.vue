<template>
  <div
    class="-all flex h-7 cursor-pointer items-center rounded pl-2 pr-1 text-gray-800 duration-300 ease-in-out"
    :class="{
      'w-full': isExpanded,
      'w-8': !isExpanded,
      'shadow-sm': isActive,
      [bgColor]: isActive,
      [hvColor]: !isActive,
    }"
    @click="handleNavigation"
  >
    <Tooltip :text="label" v-if="!isExpanded">
      <span
        class="shrink-0 text-gray-700"
        :class="{
          'text-gray-900': !isExpanded,
          'icon-emoji': isMobileView,
        }"
      >
        <Icon v-if="typeof icon === 'string'" :icon="icon" class="h-4 w-4" />
        <component :is="icon" v-else class="h-4 w-4" />
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
      <Icon v-if="typeof icon === 'string'" :icon="icon" class="h-4 w-4" />
      <component :is="icon" v-else class="h-4 w-4" />
    </span>

    <div
      class="-all ml-2 flex shrink-0 grow items-center justify-between text-sm duration-300 ease-in-out"
      :class="{
        'opacity-100': isExpanded,
        'opacity-0': !isExpanded,
        '-z-50': !isExpanded,
      }"
    >
      {{ label }}
      <slot name="right" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";
import { Icon } from "@iconify/vue";
import { useScreenSize } from "@/composables/screen";

interface P {
  icon: unknown;
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
