<template>
  <div
    ref="root"
    class="bg-surface-base px-3 pb-3 before:pointer-events-none before:absolute before:inset-x-0 before:-top-4 before:h-4 before:bg-gradient-to-t before:from-[color:var(--surface-base)] before:to-transparent sm:px-5 sm:pb-5"
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
      <Avatar :image="avatar?.image" :label="avatar?.label" size="sm" />
      <span
        class="min-w-0 truncate text-base"
        :class="draft ? 'text-ink-gray-8' : 'text-ink-gray-7'"
      >
        {{ draft || placeholder }}
      </span>
    </div>
    <!-- v-show: a drag that closes it can reopen it mid-gesture. -->
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
      <!-- pl-0.5: the avatar's centred initial lines up with the editor text. -->
      <div
        v-if="avatar?.label"
        class="flex items-center gap-2 pl-0.5 pr-2.5 pt-3"
      >
        <Avatar :image="avatar.image" :label="avatar.label" size="md" />
        <span class="truncate text-base-medium text-ink-gray-9">{{
          avatar.label
        }}</span>
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

// Releasing below this closes the editor.
const MIN_BODY_HEIGHT = 80;
const MAX_VIEWPORT_SHARE = 0.7;
// Drag stops this far below the thread top, keeping some in view.
const THREAD_PEEK = 64;
const KEY_STEP = 16;

const props = defineProps<{
  open: boolean;
  modelValue?: string;
  placeholder?: string;
  submitLabel?: string;
  submitting?: boolean;
  uploadFunction?: (file: File) => Promise<unknown>;
  accept?: string;
  avatar?: { image?: string; label?: string };
  reserve?: number;
}>();

const emit = defineEmits<{
  "update:open": [open: boolean];
  "update:modelValue": [value: string];
  "update:reserve": [height: number];
  submit: [payload: unknown];
}>();

const root = ref<HTMLElement | null>(null);

// The closed bar shows the draft on one line; blocks and breaks become spaces.
const draft = computed(() => {
  const html = (props.modelValue || "").replace(
    /<br\s*\/?>|<\/(p|div|li|h\d)>/gi,
    " "
  );
  const text = new DOMParser().parseFromString(html, "text/html").body
    .textContent;
  return (text || "").replace(/\s+/g, " ").trim();
});
const composer = ref<InstanceType<typeof CommentComposer> | null>(null);

// Keyed on the editor too: it can mount open before the editor exists.
watch(
  () => props.open && composer.value?.editor,
  (editor) => editor && composer.value?.focus(),
  { immediate: true, flush: "post" }
);

// CommentComposer has no `accept` prop; set it on the file input.
watchEffect(() => {
  const input = root.value?.querySelector<HTMLInputElement>(
    '[aria-label="Attach file"] + input[type="file"]'
  );
  if (props.accept) input?.setAttribute("accept", props.accept);
  else input?.removeAttribute("accept");
});
// 0 = natural height.
const height = useStorage("kb:composer-height", 0);
const { height: viewportHeight } = useWindowSize();

const resizing = ref<{
  startY: number;
  startHeight: number;
  minY: number;
  closed: boolean;
} | null>(null);
const isResizing = computed(() => resizing.value !== null);

// A resized composer overlays the thread: the reserve stays at the last
// unresized height (the closed bar or the natural editor), or less. The saved
// height sizes only the open editor, so the closed bar always counts in full.
const { height: composerHeight } = useElementSize(root, undefined, {
  box: "border-box",
});
let baseReserve = 0;
watch(
  [composerHeight, () => props.open && height.value > 0],
  ([value, resized]) => {
    if (!resized) baseReserve = value;
    emit(
      "update:reserve",
      Math.round(resized ? Math.min(value, baseReserve) : value)
    );
  },
  { immediate: true }
);

// Clamped on read: a saved height may not fit this window.
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
  // Capture on root so the drag keeps its cursor and events.
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
