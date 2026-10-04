<template>
  <div
    v-if="items.length && collapsible"
    class="rounded-4 border border-outline-gray-2"
  >
    <button
      type="button"
      class="flex h-10 w-full items-center justify-between gap-2 px-3 text-left text-base text-ink-gray-8"
      :aria-expanded="isOpen"
      @click="isOpen = !isOpen"
    >
      {{ __("On this page") }}
      <span
        class="lucide-chevron-down size-4 shrink-0 text-ink-gray-5 transition-transform duration-150"
        :class="isOpen && 'rotate-180'"
      />
    </button>
    <PortalCollapse :open="isOpen">
      <nav class="flex flex-col px-3 pb-3">
        <button
          v-for="item in items"
          :key="item.id"
          type="button"
          class="border-l py-2 pl-3 text-left text-[14px] leading-normal text-ink-gray-6"
          :class="
            item.id === activeId
              ? 'border-ink-gray-9 text-ink-gray-9'
              : 'border-outline-gray-1'
          "
          @click="scrollTo(item.id)"
        >
          {{ item.text }}
        </button>
      </nav>
    </PortalCollapse>
  </div>
  <nav v-else-if="items.length" class="flex flex-col">
    <button
      v-for="item in items"
      :key="item.id"
      type="button"
      class="border-l py-[7px] pl-3 text-left text-[14px] leading-normal tracking-[0.28px] transition-colors"
      :class="
        item.id === activeId
          ? 'border-ink-gray-9 text-ink-gray-9'
          : 'border-outline-gray-1 text-ink-gray-5 hover:border-outline-gray-3 hover:text-ink-gray-7'
      "
      @click="scrollTo(item.id)"
    >
      {{ item.text }}
    </button>
  </nav>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { useEventListener } from "@vueuse/core";
import { __ } from "@helpdesk/shared/translation";
import PortalCollapse from "@app/components/common/PortalCollapse.vue";

// A fraction, not a fixed offset, so every heading of a short article can become current.
const ACTIVE_RATIO = 0.25;

// `collapsible` folds the list behind a toggle, for screens without a side column.
const props = withDefaults(
  defineProps<{
    items?: { id: string; text: string }[];
    collapsible?: boolean;
  }>(),
  { items: () => [], collapsible: false }
);

const isOpen = ref(false);
const activeId = ref<string | null>(null);

function measure(scrolled?: EventTarget | null) {
  const box = scrolled instanceof HTMLElement ? scrolled : null;
  // At the end of the scroll the last section is usually too short to reach the line.
  if (box && box.scrollTop + box.clientHeight >= box.scrollHeight - 4) {
    activeId.value = props.items.at(-1)?.id ?? null;
    return;
  }
  const line = window.innerHeight * ACTIVE_RATIO;
  let current = props.items[0]?.id ?? null;
  for (const item of props.items) {
    const top = document.getElementById(item.id)?.getBoundingClientRect().top;
    if (top !== undefined && top <= line) current = item.id;
  }
  activeId.value = current;
}

function scrollTo(id: string) {
  // Instant on purpose: Chrome drops smooth scrolls under an overflow-hidden ancestor.
  document.getElementById(id)?.scrollIntoView({ block: "start" });
}

// Captured, since scroll does not bubble: this hears the nested body scroller.
useEventListener(document, "scroll", (event) => measure(event.target), {
  capture: true,
  passive: true,
});
useEventListener(window, "resize", () => measure());
watch(
  () => props.items,
  () => measure(),
  { flush: "post" }
);
onMounted(() => measure());
</script>
