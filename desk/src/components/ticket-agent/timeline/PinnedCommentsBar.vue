<template>
  <button
    v-if="comments.length"
    type="button"
    class="flex shrink-0 items-center gap-2.5 bg-surface-gray-1 px-5 py-2 text-left"
    :aria-label="__('Go to pinned comment {0}', [current + 1])"
    @click="select"
  >
    <!-- one full-height line split evenly per pin; past two pins -my-0.5
    reaches into the padding so the segments stay tall enough to read -->
    <span
      class="relative flex flex-col gap-0.5 self-stretch"
      :class="{ '-my-0.5': comments.length > 2 }"
    >
      <span
        v-for="comment in comments"
        :key="comment.name"
        class="w-[3px] flex-1 rounded-full bg-surface-gray-4"
      />
      <span
        class="absolute inset-x-0 rounded-full bg-surface-violet-6 motion-safe:transition-[top] motion-safe:duration-150 motion-safe:ease-out"
        :style="indicatorStyle"
      />
    </span>
    <!-- -top-px optically centres Inter, whose glyphs sit low -->
    <span class="relative -top-px flex min-w-0 flex-1 items-center gap-2">
      <PinIcon class="size-4 shrink-0 text-ink-gray-8" />
      <!-- one grid cell, so the leaving and entering previews overlap while they slide -->
      <span class="grid min-w-0 flex-1 overflow-hidden">
        <Transition
          enter-active-class="motion-safe:transition motion-safe:duration-150 motion-safe:ease-out"
          leave-active-class="motion-safe:transition motion-safe:duration-150 motion-safe:ease-out"
          :enter-from-class="`opacity-0 ${
            toOlder ? '-translate-y-full' : 'translate-y-full'
          }`"
          :leave-to-class="`opacity-0 ${
            toOlder ? 'translate-y-full' : '-translate-y-full'
          }`"
        >
          <p
            :key="current"
            class="truncate text-p-base text-ink-gray-5 [grid-area:1/1]"
          >
            <span class="font-medium text-ink-gray-7">{{ current + 1 }}:</span>
            {{ preview }}
          </p>
        </Transition>
      </span>
    </span>
  </button>
</template>

<script setup lang="ts">
import { PinIcon } from "@/components/icons";
import type { PinnedComment } from "@/composables/useTicket";
import { htmlToText } from "@/utils";
import { computed, ref, watch } from "vue";

/**
 * Telegram-style pinned bar: shows one pin at a time, newest first. A click
 * waits for `jump` to reach the shown pin, then steps to the next older one.
 */
const props = defineProps<{
  comments: PinnedComment[];
  jump: (name: string) => Promise<void>;
}>();

const SEGMENT_GAP = "2px";
// pause after the jump lands before the bar steps on, so the move reads as a result
const ADVANCE_DELAY_MS = 300;

const current = ref(props.comments.length - 1);
let jumping = false;
// older pins sit higher in the feed, so their preview slides in from above
const toOlder = ref(true);

const preview = computed(() =>
  htmlToText(props.comments[current.value]?.content ?? "")
    .replace(/\s+/g, " ")
    .trim()
);

// the violet piece covers segment `current` of the gray track and glides between them
const indicatorStyle = computed(() => {
  const count = props.comments.length;
  return {
    top: `calc(${current.value} * (100% + ${SEGMENT_GAP}) / ${count})`,
    height: `calc((100% - ${count - 1} * ${SEGMENT_GAP}) / ${count})`,
  };
});

async function select() {
  const pin = props.comments[current.value];
  if (jumping || !pin) return;
  jumping = true;
  try {
    await props.jump(pin.name);
    await new Promise((resolve) => setTimeout(resolve, ADVANCE_DELAY_MS));
    toOlder.value = current.value > 0;
    const count = props.comments.length;
    current.value = (current.value - 1 + count) % count;
  } finally {
    jumping = false;
  }
}

watch(
  () => props.comments.length,
  (count) => (current.value = count - 1)
);
</script>
