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
      <nav class="flex flex-col px-3 pb-3 text-base">
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
  <nav
    v-else-if="items.length"
    ref="rail"
    class="flex max-h-[calc(100vh-8rem)] flex-col overflow-y-auto pb-10 text-base [mask-image:linear-gradient(to_bottom,black_calc(100%-2.5rem),transparent)] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
  >
    <!-- Transparent border aligns the label; h-6 matches the Copy for LLM button. -->
    <span
      class="flex h-6 shrink-0 items-center border-l border-transparent pl-4 font-medium text-ink-gray-8"
    >
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
import { useRoute } from "vue-router";
import { __ } from "@helpdesk/shared/translation";
import { findArticleHeading } from "@helpdesk/shared/utils";
import PortalCollapse from "@app/components/ui/PortalCollapse.vue";

const ACTIVE_RATIO = 1 / 3;
// Within this many px of the top, the first heading is current.
const TOP_ZONE = 100;

type Item = { id: string; text: string; level: number };

const props = withDefaults(
  defineProps<{ items?: Item[]; collapsible?: boolean }>(),
  { items: () => [], collapsible: false }
);

const isOpen = ref(false);
const activeId = ref<string | null>(null);
const rail = ref<HTMLElement | null>(null);
// A clicked heading stays current until the reader scrolls.
let pinnedId: string | null = null;

// Indent relative to the shallowest level, so flat lists align.
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
      const top = findArticleHeading(item.id)?.getBoundingClientRect().top;
      if (top !== undefined && top <= line) current = item.id;
    }
  }
  activeId.value = current;
}

function scrollTo(id: string) {
  pinnedId = activeId.value = id;
  // Instant on purpose: Chrome drops smooth scrolls under an overflow-hidden ancestor.
  findArticleHeading(id)?.scrollIntoView({ block: "start" });
}

// Scroll the rail by hand: scrollIntoView would move the page.
watch(activeId, async (id) => {
  if (!id) return;
  await nextTick();
  const nav = rail.value;
  const link = nav?.querySelector<HTMLElement>(
    `[data-toc-id="${CSS.escape(id)}"]`
  );
  if (!nav || !link) return;
  if (link.offsetTop < nav.scrollTop) nav.scrollTop = link.offsetTop;
  else if (
    link.offsetTop + link.offsetHeight >
    nav.scrollTop + nav.clientHeight
  )
    nav.scrollTop = link.offsetTop + link.offsetHeight - nav.clientHeight;
});

// Capture: scroll doesn't bubble from the nested scroller.
useEventListener(
  document,
  "scroll",
  (event) => {
    // Only the article's scroller, not sidebars or this rail.
    const first = findArticleHeading(props.items[0]?.id ?? "");
    if (event.target instanceof Node && event.target.contains(first))
      measure(event.target);
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
// A heading's "#" link sets the hash: that heading is current, as if clicked here.
const route = useRoute();
watch(
  () => [route.hash, props.items] as const,
  ([hash, items]) => {
    const id = hash.slice(1);
    if (items.some((item) => item.id === id)) pinnedId = activeId.value = id;
  },
  { immediate: true }
);
onMounted(() => measure());
</script>
