<template>
  <div
    class="-all flex h-7 cursor-pointer items-center rounded pl-2 pr-1 duration-300 ease-in-out"
    :class="linkClasses"
    @click="handleNavigation"
  >
    <Tooltip :text="label" v-if="!isExpanded">
      <span
        class="shrink-0"
        :class="[iconClasses, isMobileView ? 'icon-emoji' : '']"
      >
        <component :is="icon" class="h-4 w-4" />
      </span>
    </Tooltip>
    <span
      v-else
      class="shrink-0"
      :class="[iconClasses, isMobileView ? 'icon-emoji' : '']"
    >
      <component :is="icon" class="h-4 w-4" />
    </span>

    <div
      class="-all ml-2 flex shrink-0 grow items-center justify-between text-sm duration-300 ease-in-out"
      :class="[
        textClasses,
        {
          'opacity-100': isExpanded,
          'opacity-0': !isExpanded,
          '-z-50': !isExpanded,
        },
      ]"
    >
      {{ label }}
      <slot name="right" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useScreenSize } from "@/composables/screen";
import { useRouter } from "vue-router";
import { computed } from "vue";

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
  hvColor: "hover:bg-white/10",
});
const router = useRouter();
const { isMobileView } = useScreenSize();

const linkClasses = computed(() =>
  [
    props.isExpanded ? "w-full" : "w-8",
    props.isActive
      ? ["shadow-sm", "text-ink-gray-9"]
      : ["text-ink-gray-1", "hover:text-ink-white"],
    props.isActive ? props.bgColor : props.hvColor,
  ].flat()
);

const textClasses = computed(() =>
  props.isActive ? "text-ink-gray-9" : "text-ink-gray-1"
);

const iconClasses = computed(() =>
  props.isActive ? "text-ink-gray-9" : "text-ink-gray-1"
);

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
