<template>
  <!-- px-4 lives once here so the header and content share a single horizontal
       padding instead of each declaring their own. -->
  <div class="px-4">
    <slot name="header" v-bind="{ opened, hide, open, close, toggle }">
      <div
        v-if="!hide"
        class="section-header sticky top-0 z-10 flex cursor-pointer select-none items-center gap-1 bg-surface-base py-3.5"
        :class="headerClass"
        @click="collapsible && toggle()"
      >
        <Tooltip v-if="tooltip" :text="__(tooltip)">
          <span class="text-base-semibold text-ink-gray-8" :class="labelClass">
            {{ __(label) || "Untitled" }}
          </span>
        </Tooltip>
        <span
          v-else
          class="text-base-semibold text-ink-gray-8"
          :class="labelClass"
        >
          {{ __(label) || "Untitled" }}
        </span>
        <LucideChevronRight
          v-if="collapsible"
          class="size-3.5 text-ink-gray-6 transition-transform"
          :class="{ 'rotate-90': opened }"
        />
        <slot name="actions"></slot>
      </div>
    </slot>
    <transition
      enter-active-class="duration-300 ease-in"
      leave-active-class="duration-300 ease-[cubic-bezier(0, 1, 0.5, 1)]"
      enter-to-class="max-h-[2000px] overflow-hidden"
      leave-from-class="max-h-[2000px] overflow-hidden"
      enter-from-class="max-h-0 opacity-0"
      leave-to-class="max-h-0 opacity-0"
    >
      <div class="columns" v-bind="$attrs" v-show="opened">
        <slot v-bind="{ opened, open, close, toggle }" />
      </div>
    </transition>
  </div>
</template>
<script setup>
import { __ } from "@/translation";
import { Tooltip } from "frappe-ui";
import { ref, watch } from "vue";
import LucideChevronRight from "~icons/lucide/chevron-right";

const props = defineProps({
  label: {
    type: String,
    default: "",
  },
  tooltip: {
    type: String,
    default: "",
  },
  hideLabel: {
    type: Boolean,
    default: false,
  },
  opened: {
    type: Boolean,
    default: true,
  },
  collapsible: {
    type: Boolean,
    default: true,
  },
  labelClass: {
    type: [String, Object, Array],
    default: "",
  },
  headerClass: {
    type: [String, Object, Array],
    default: "",
  },
});

const emit = defineEmits(["update:opened"]);

const hide = ref(props.hideLabel);
const opened = ref(props.opened);

watch(
  () => props.opened,
  (val) => {
    opened.value = val;
  }
);

function setOpened(value) {
  opened.value = value;
  emit("update:opened", value);
}

function toggle() {
  setOpened(!opened.value);
}

function open() {
  setOpened(true);
}

function close() {
  setOpened(false);
}
</script>
<script>
export default {
  inheritAttrs: false,
};
</script>
