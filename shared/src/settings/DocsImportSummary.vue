<template>
  <!-- Every page added: nothing to break down, so no bar -->
  <p v-if="allAdded" class="flex items-start gap-2 text-p-base text-ink-gray-8">
    <LucideCircleCheck
      class="mt-0.5 size-4 shrink-0 text-ink-green-5"
      aria-hidden="true"
    />
    {{ successText }}
  </p>
  <div v-else class="space-y-5">
    <div class="space-y-1">
      <p class="text-lg-semibold text-ink-gray-9">{{ title }}</p>
      <p class="text-p-sm text-ink-gray-6">{{ subtitle }}</p>
    </div>
    <div
      class="flex h-2 gap-0.5 overflow-hidden rounded-full"
      role="img"
      :aria-label="barLabel"
    >
      <div
        v-for="part in parts.filter((p) => p.value)"
        :key="part.label"
        :class="part.color"
        :style="{ flexGrow: part.value }"
      />
    </div>
    <ul class="flex flex-wrap gap-x-4 gap-y-2">
      <li
        v-for="part in parts"
        :key="part.label"
        class="flex items-center gap-1.5"
      >
        <span
          :class="part.color"
          class="size-1.5 shrink-0 rounded-full"
          aria-hidden="true"
        />
        <span class="text-sm text-ink-gray-6">
          <span class="text-sm-medium tabular-nums text-ink-gray-9">{{
            part.value
          }}</span>
          {{ part.label }}
        </span>
      </li>
    </ul>
    <details
      v-if="result.unreadable?.length"
      class="group rounded-lg border border-outline-gray-2"
    >
      <summary
        class="flex cursor-pointer list-none items-center gap-2 rounded-lg px-3 py-2.5 hover:bg-surface-gray-1 [&::-webkit-details-marker]:hidden"
      >
        <LucideFileX
          class="size-4 shrink-0 text-ink-red-5"
          aria-hidden="true"
        />
        <span class="flex-1 text-base text-ink-gray-8">{{
          unreadableTitle
        }}</span>
        <LucideChevronDown
          class="size-4 text-ink-gray-5 group-open:rotate-180"
          aria-hidden="true"
        />
      </summary>
      <ul
        class="max-h-48 space-y-2 overflow-y-auto border-t border-outline-gray-2 px-3 py-2"
      >
        <li v-for="page in result.unreadable" :key="page.url" class="min-w-0">
          <a
            :href="page.url"
            target="_blank"
            rel="noopener noreferrer"
            class="block truncate text-sm text-ink-gray-8 hover:underline"
            :title="page.url"
            >{{ pathOf(page.url) }}</a
          >
          <p class="text-p-xs text-ink-gray-5">
            {{ reasonText[page.reason] ?? reasonText.failed }}
          </p>
        </li>
      </ul>
    </details>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import LucideChevronDown from "~icons/lucide/chevron-down";
import LucideCircleCheck from "~icons/lucide/circle-check";
import LucideFileX from "~icons/lucide/file-x";
import { __ } from "../translation";
import type { ImportResult } from "./docsImport";

const props = defineProps<{
  result: Extract<ImportResult, { state: "done" }>;
  categoryLabel?: string;
}>();

const reasonText: Record<string, string> = {
  not_found: __("Page not found"),
  blocked: __("The site blocked us"),
  timed_out: __("Took too long to load"),
  server_error: __("The site returned an error"),
  empty: __("No text on the page"),
  not_html: __("Not a web page"),
  too_large: __("The page is too large"),
  failed: __("Couldn't copy the page"),
};

const parts = computed(() => [
  {
    label: __("new"),
    value: props.result.created,
    color: "bg-surface-gray-8",
  },
  {
    label: __("skipped"),
    value: props.result.skipped,
    color: "bg-surface-gray-5",
  },
  {
    label: __("failed"),
    value: props.result.failed,
    color: "bg-surface-red-6",
  },
]);

const total = computed(() =>
  parts.value.reduce((sum, part) => sum + part.value, 0)
);

const allAdded = computed(
  () => props.result.created > 0 && props.result.created === total.value
);

const successText = computed(() => {
  const { created } = props.result;
  const label = props.categoryLabel;
  if (created === 1)
    return label
      ? __("Imported 1 page as a draft in {0}.", [label])
      : __("Imported 1 page as a draft.");
  return label
    ? __("Imported {0} pages as drafts in {1}.", [created, label])
    : __("Imported {0} pages as drafts.", [created]);
});

const title = computed(() =>
  total.value === 1
    ? __("1 page checked on {0}", [props.result.host])
    : __("{0} pages checked on {1}", [total.value, props.result.host])
);

const subtitle = computed(() => {
  if (!props.result.created) return __("Everything there is already imported.");
  return props.categoryLabel
    ? __("The new pages are drafts in {0}.", [props.categoryLabel])
    : __("The new pages are drafts.");
});

const barLabel = computed(() =>
  parts.value.map((part) => `${part.value} ${part.label}`).join(", ")
);

const unreadableTitle = computed(() => {
  const count = props.result.unreadable?.length ?? 0;
  return count === 1
    ? __("1 page couldn't be read")
    : __("{0} pages couldn't be read", [count]);
});

function pathOf(url: string) {
  try {
    return new URL(url).pathname;
  } catch {
    return url;
  }
}
</script>
