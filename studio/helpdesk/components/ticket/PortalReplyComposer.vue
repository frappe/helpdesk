<template>
  <div
    ref="root"
    class="bg-surface-base px-3 pb-3 sm:px-5 sm:pb-5"
    :class="{ 'cursor-ns-resize': isResizing }"
  >
    <div
      v-show="!open"
      role="button"
      tabindex="0"
      class="flex cursor-pointer items-center gap-2 rounded-6 border border-outline-gray-2 bg-surface-gray-2 px-3.5 py-2 hover:bg-surface-gray-3 focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
      @click="emit('update:open', true)"
      @keydown.enter.prevent="emit('update:open', true)"
      @keydown.space.prevent="emit('update:open', true)"
    >
      <Avatar
        :image="avatar?.image"
        :label="avatar?.label"
        size="sm"
        class="has-[>div:first-child]:border has-[>div:first-child]:border-outline-gray-2"
      />
      <span class="text-base text-ink-gray-7">{{ placeholder }}</span>
    </div>
    <!-- Hidden, not unmounted: a drag that closes the editor can reopen it in the same gesture. -->
    <div
      v-show="open"
      class="portal-reply-composer group/composer relative rounded-6 border border-outline-gray-2 bg-surface-elevation-1 px-3"
      :class="{ 'is-resized': height > 0 }"
      :style="bodyStyle"
    >
      <div
        role="separator"
        aria-orientation="horizontal"
        tabindex="0"
        class="absolute -top-0.5 left-1/2 z-10 hidden h-6 w-24 -translate-x-1/2 cursor-ns-resize touch-none items-center justify-center rounded-full opacity-60 transition-opacity hover:opacity-100 focus:opacity-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3 group-hover/composer:opacity-100 sm:flex"
        :aria-label="__('Resize composer')"
        @pointerdown.stop.prevent="startResize"
        @keydown.up.prevent="resizeBy(KEY_STEP)"
        @keydown.down.prevent="resizeBy(-KEY_STEP)"
      >
        <span class="h-1 w-10 rounded-full bg-surface-gray-4" />
      </div>
      <CommentComposer
        ref="composer"
        :model-value="modelValue"
        :placeholder="placeholder"
        :submit-label="submitLabel"
        :submitting="submitting"
        :upload-function="uploadFunction"
        @update:model-value="emit('update:modelValue', $event)"
        @submit="emit('submit', { ...$event, reset: () => composer?.reset() })"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, watchEffect } from "vue";
import {
  useElementSize,
  useEventListener,
  useStorage,
  useWindowSize,
} from "@vueuse/core";
import { Avatar } from "frappe-ui";
import { CommentComposer } from "@framework/ui/components/Composer";
import { __ } from "@helpdesk/shared/translation";

// Below this the editor is too short to type in, so letting go there closes it.
const MIN_BODY_HEIGHT = 80;
const MAX_VIEWPORT_SHARE = 0.7;
// The drag stops this far below the top of the thread, so some of it stays in view.
const THREAD_PEEK = 64;
const KEY_STEP = 16;

const props = defineProps<{
  open: boolean;
  modelValue?: string;
  placeholder?: string;
  submitLabel?: string;
  submitting?: boolean;
  uploadFunction?: (file: File) => Promise<unknown>;
  // File types the attach button offers; empty allows any.
  accept?: string;
  avatar?: { image?: string; label?: string };
  // The room the thread keeps clear under the composer.
  reserve?: number;
}>();

const emit = defineEmits<{
  "update:open": [open: boolean];
  "update:modelValue": [value: string];
  "update:reserve": [height: number];
  submit: [payload: unknown];
}>();

const root = ref<HTMLElement | null>(null);
const composer = ref<InstanceType<typeof CommentComposer> | null>(null);

// CommentComposer has no prop for this, so it goes straight onto its hidden file input.
watchEffect(() => {
  const input = root.value?.querySelector<HTMLInputElement>(
    '[aria-label="Attach file"] + input[type="file"]'
  );
  if (props.accept) input?.setAttribute("accept", props.accept);
  else input?.removeAttribute("accept");
});
// Per browser, like the desk's; 0 leaves the editor at its natural height.
const height = useStorage("kb:composer-height", 0);
const { height: viewportHeight } = useWindowSize();

const resizing = ref<{
  startY: number;
  startHeight: number;
  minY: number;
  closed: boolean;
} | null>(null);
const isResizing = computed(() => resizing.value !== null);

// Held while the drag grows the composer, so it slides over the thread instead of pushing it up;
// a shrinking composer hands the room straight back, or the thread would end above a blank band.
const { height: composerHeight } = useElementSize(root, undefined, {
  box: "border-box",
});
watch(
  [composerHeight, () => resizing.value],
  ([value, drag]) => {
    if (!drag || value < (props.reserve ?? 0))
      emit("update:reserve", Math.round(value));
  },
  { immediate: true }
);

// Clamped on read too, so a height saved on a taller window still fits this one.
const bodyStyle = computed(() =>
  height.value > 0
    ? { "--composer-body-height": `${clamp(height.value)}px` }
    : undefined
);

function clamp(value: number) {
  const floor = isResizing.value ? 0 : MIN_BODY_HEIGHT;
  return Math.min(
    Math.max(value, floor),
    Math.round(viewportHeight.value * MAX_VIEWPORT_SHARE)
  );
}

function startResize(event: PointerEvent) {
  const handle = event.currentTarget as HTMLElement;
  resizing.value = {
    startY: event.clientY,
    startHeight: currentHeight(),
    minY: threadTop() + (event.clientY - handle.getBoundingClientRect().top),
    closed: false,
  };
  // Captured on the root, so the drag keeps its cursor and events off the handle and the window.
  try {
    (root.value ?? handle).setPointerCapture(event.pointerId);
  } catch {}
}

function threadTop() {
  const thread = document.querySelector(".activity-timeline");
  return thread ? thread.getBoundingClientRect().top + THREAD_PEEK : 0;
}

function currentHeight() {
  if (height.value) return clamp(height.value);
  return (
    root.value?.querySelector<HTMLElement>(".composer-body")?.offsetHeight ?? 0
  );
}

function resizeBy(delta: number) {
  height.value = clamp(currentHeight() + delta);
}

useEventListener(window, "pointermove", (event: PointerEvent) => {
  if (!resizing.value) return;
  const { startY, startHeight, minY, closed } = resizing.value;
  const next = startHeight + (startY - Math.max(event.clientY, minY));
  if (next <= 0) {
    if (!closed) {
      resizing.value.closed = true;
      height.value = clamp(startHeight);
      emit("update:open", false);
    }
    return;
  }
  if (closed) {
    resizing.value.closed = false;
    emit("update:open", true);
  }
  height.value = clamp(next);
});
useEventListener(window, "pointerup", stopResize);
useEventListener(window, "pointercancel", stopResize);

function stopResize() {
  if (!resizing.value) return;
  const { startHeight, closed } = resizing.value;
  const squeezed = !closed && height.value < MIN_BODY_HEIGHT;
  resizing.value = null;
  if (!squeezed) return;
  height.value = clamp(startHeight);
  emit("update:open", false);
}
</script>

<style>
.portal-reply-composer.is-resized .composer-body {
  max-height: none;
  flex: 1 1 auto;
  height: var(--composer-body-height);
}
</style>
