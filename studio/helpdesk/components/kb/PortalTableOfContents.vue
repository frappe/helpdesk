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
      <nav class="flex flex-col px-3 pb-3 text-base leading-relaxed">
        <button
          v-for="item in items"
          :key="item.id"
          type="button"
          :class="linkClass(item)"
          @click="scrollTo(item.id)"
        >
          {{ item.text }}
        </button>
      </nav>
    </PortalCollapse>
  </div>
  <!-- As on Frappe Wiki: a label, then a faint rail whose active segment darkens. -->
  <nav
    v-else-if="items.length"
    ref="rail"
    class="flex max-h-[calc(100vh-8rem)] flex-col overflow-y-auto text-base leading-relaxed [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
  >
    <!-- The transparent rail keeps the label on the links' left edge. -->
    <span class="border-l border-transparent pb-1 pl-4 font-medium text-ink-gray-8">
      {{ __("On this page") }}
    </span>
    <button
      v-for="item in items"
      :key="item.id"
      type="button"
      :data-toc-id="item.id"
      :class="linkClass(item)"
      @click="scrollTo(item.id)"
    >
      {{ item.text }}
    </button>
  </nav>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from "vue";
import { useEventListener } from "@vueuse/core";
import { __ } from "@helpdesk/shared/translation";
import PortalCollapse from "@app/components/common/PortalCollapse.vue";

// A heading is current once it crosses the top third of the viewport.
const ACTIVE_RATIO = 1 / 3;
// Near the top the first heading is current, even before it reaches the line.
const TOP_ZONE = 100;

type Item = { id: string; text: string; level: number };

// `collapsible` folds the list behind a toggle, for screens without a side column.
const props = withDefaults(
  defineProps<{ items?: Item[]; collapsible?: boolean }>(),
  { items: () => [], collapsible: false }
);

const isOpen = ref(false);
const activeId = ref<string | null>(null);
const rail = ref<HTMLElement | null>(null);
// A clicked heading stays current until the reader scrolls on their own.
let pinnedId: string | null = null;

// Deeper headings indent only when shallower ones exist, so a flat list stays aligned.
const topLevel = computed(() =>
  Math.min(...props.items.map((item) => item.level))
);

function linkClass(item: Item) {
  return [
    "border-l py-1 text-left",
    item.level > topLevel.value ? "pl-7" : "pl-4",
    item.id === activeId.value
      ? "border-outline-gray-7 text-ink-gray-9"
      : "border-outline-gray-1 text-ink-gray-6 hover:text-ink-gray-9",
  ];
}

function measure(scrolled?: EventTarget | null) {
  if (pinnedId) return;
  const box = scrolled instanceof HTMLElement ? scrolled : null;
  let current = props.items[0]?.id ?? null;
  if (!box || box.scrollTop >= TOP_ZONE) {
    const line = window.innerHeight * ACTIVE_RATIO;
    for (const item of props.items) {
      const top = document.getElementById(item.id)?.getBoundingClientRect().top;
      if (top !== undefined && top <= line) current = item.id;
    }
  }
  activeId.value = current;
}

function scrollTo(id: string) {
  pinnedId = activeId.value = id;
  // Instant on purpose: Chrome drops smooth scrolls under an overflow-hidden ancestor.
  document.getElementById(id)?.scrollIntoView({ block: "start" });
}

// A long list scrolls on its own; scrolled by hand, since scrollIntoView would move the page.
watch(activeId, async (id) => {
  await nextTick();
  const nav = rail.value;
  const link = nav?.querySelector<HTMLElement>(`[data-toc-id="${id}"]`);
  if (!nav || !link) return;
  if (link.offsetTop < nav.scrollTop) nav.scrollTop = link.offsetTop;
  else if (link.offsetTop + link.offsetHeight > nav.scrollTop + nav.clientHeight)
    nav.scrollTop = link.offsetTop + link.offsetHeight - nav.clientHeight;
});

// Captured, since scroll does not bubble: this hears the nested body scroller.
useEventListener(
  document,
  "scroll",
  (event) => {
    // Only the scroller holding the article moves its headings; not the sidebars or this rail.
    const first = document.getElementById(props.items[0]?.id ?? "");
    if (event.target instanceof Node && event.target.contains(first)) measure(event.target);
  },
  { capture: true, passive: true }
);
useEventListener(window, "resize", () => measure());
for (const event of ["wheel", "touchmove", "keydown"]) {
  useEventListener(window, event, () => (pinnedId = null), { passive: true });
}
watch(
  () => props.items,
  () => measure(),
  { flush: "post" }
);
onMounted(() => measure());
</script>
