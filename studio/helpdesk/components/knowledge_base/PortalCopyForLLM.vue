<template>
  <div v-if="compact" class="flex shrink-0">
    <Dropdown :options="compactOptions" align="end">
      <template #trigger>
        <Button
          variant="ghost"
          icon="lucide-more-horizontal"
          :aria-label="__('Article actions')"
          @pointerdown="load"
          @focus="load"
        />
      </template>
      <template #item-suffix="{ item }">
        <span
          v-if="item.external"
          class="lucide-arrow-up-right size-3.5 shrink-0 text-ink-gray-5"
        />
      </template>
    </Dropdown>
  </div>
  <div v-else class="flex shrink-0 items-center">
    <Button
      size="xs"
      variant="outline"
      class="rounded-e-none"
      :label="__('Copy for LLM')"
      icon-left="lucide-copy"
      @pointerdown="load"
      @focus="load"
      @click="copyMarkdown"
    />
    <Dropdown :options="options" align="end">
      <template #trigger>
        <Button
          size="xs"
          variant="outline"
          class="-ms-px rounded-s-none"
          icon="lucide-chevron-down"
          :aria-label="__('More ways to use this article with an LLM')"
          @pointerdown="load"
          @focus="load"
        />
      </template>
      <template #item-suffix="{ item }">
        <span
          v-if="item.external"
          class="lucide-arrow-up-right size-3.5 shrink-0 text-ink-gray-5"
        />
      </template>
    </Dropdown>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useClipboard } from "@vueuse/core";
import { Button, Dropdown, toast } from "frappe-ui";
import { __ } from "@helpdesk/shared/translation";
import { copyPageLink } from "@app/utils";

const MARKDOWN_METHOD =
  "/api/method/helpdesk.api.knowledge_base.get_article_markdown";

const props = withDefaults(
  defineProps<{
    name: string;
    isPublic?: boolean;
    compact?: boolean;
  }>(),
  { isPublic: false, compact: false }
);

// `legacy`: execCommand fallback where the Clipboard API is missing (plain http).
const { copy } = useClipboard({ legacy: true });

// Fetched on the press or focus before the click, not on every article open: Safari drops a
// clipboard write that waits on the network, and most readers never copy.
const markdown = ref("");
let request: Promise<void> | null = null;
const markdownUrl = computed(
  () =>
    `${window.location.origin}${MARKDOWN_METHOD}?name=${encodeURIComponent(
      props.name
    )}`
);

watch(
  () => props.name,
  () => {
    markdown.value = "";
    request = null;
  }
);

function load() {
  const name = props.name;
  if (!name) return Promise.resolve();
  request ||= fetch(markdownUrl.value)
    .then(async (response) => {
      if (!response.ok) return;
      const text = await response.text();
      // the page reuses this component across articles; drop a late answer for the previous one
      if (name === props.name) markdown.value = text;
    })
    .catch(() => {});
  return request;
}

async function copyMarkdown() {
  if (!markdown.value) await load();
  if (!markdown.value) {
    request = null;
    toast.error(__("Could not copy the article"));
    return;
  }
  await copy(markdown.value);
  toast.success(__("Copied as Markdown"));
}

function openInAssistant(baseUrl: string) {
  const prompt = __("Read {0} so I can ask questions about it.", [
    markdownUrl.value,
  ]);
  window.open(`${baseUrl}${encodeURIComponent(prompt)}`, "_blank", "noopener");
}

const viewOptions = computed(() => [
  {
    label: __("View as Markdown"),
    icon: "lucide-file-text",
    external: true,
    onClick: () => window.open(markdownUrl.value, "_blank", "noopener"),
  },
  {
    label: __("Open in ChatGPT"),
    icon: "lucide-message-circle",
    external: true,
    condition: () => props.isPublic,
    onClick: () => openInAssistant("https://chatgpt.com/?hints=search&q="),
  },
  {
    label: __("Open in Claude"),
    icon: "lucide-sparkles",
    external: true,
    condition: () => props.isPublic,
    onClick: () => openInAssistant("https://claude.ai/new?q="),
  },
]);

const options = computed(() => [
  { label: __("Copy as Markdown"), icon: "lucide-copy", onClick: copyMarkdown },
  ...viewOptions.value,
]);

const compactOptions = computed(() => [
  {
    group: "Copy",
    hideLabel: true,
    options: [
      { label: __("Copy for LLM"), icon: "lucide-copy", onClick: copyMarkdown },
      { label: __("Copy link"), icon: "lucide-link", onClick: copyPageLink },
    ],
  },
  { group: "Open", hideLabel: true, options: viewOptions.value },
]);
</script>
