<template>
  <div class="flex flex-col gap-3">
    <div
      class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between sm:gap-4"
    >
      <div class="flex min-w-0 flex-col">
        <h3 class="text-base-medium text-ink-gray-8">
          {{ __("Copy pages from your docs site") }}
        </h3>
        <span class="mt-1 text-base leading-5 text-ink-gray-6">
          {{
            __(
              "Paste your docs address and pick a category. Up to 50 pages are copied once as drafts you can edit and publish."
            )
          }}
        </span>
      </div>
      <Button
        class="shrink-0 self-start"
        :label="__('Import pages')"
        @click="open = true"
      />
    </div>

    <button
      v-if="result?.state === 'running'"
      type="button"
      class="flex min-h-11 w-full items-center gap-2.5 rounded-5 border border-outline-gray-2 px-3 text-left text-p-base text-ink-gray-7 hover:bg-surface-gray-1 sm:min-h-10"
      @click="open = true"
    >
      <span
        class="lucide-loader-circle size-4 shrink-0 animate-spin text-ink-gray-6 motion-reduce:animate-none"
        aria-hidden="true"
      />
      <span
        class="min-w-0 flex-1 truncate"
        :title="result.host"
        aria-live="polite"
      >
        {{ runningLine }}
      </span>
    </button>

    <div
      v-else-if="result?.state === 'done'"
      class="flex min-h-11 items-center gap-2.5 rounded-5 border border-outline-gray-2 px-3 text-p-base text-ink-gray-7 sm:min-h-10"
    >
      <span
        class="lucide-check size-4 shrink-0 text-ink-gray-6"
        aria-hidden="true"
      />
      <span class="min-w-0 flex-1 truncate" :title="doneLine">
        {{ doneLine }}
      </span>
      <a
        v-if="result.created"
        :href="viewDraftsHref(result.category)"
        class="shrink-0 text-ink-gray-8 underline underline-offset-2"
      >
        {{ __("View drafts") }}
      </a>
    </div>

    <DocsImportDialog v-model:open="open" @started="refresh" />
  </div>
</template>

<script setup lang="ts">
import { Button } from "frappe-ui";
import { computed, onMounted, ref, watch } from "vue";
import { __ } from "../translation";
import DocsImportDialog from "./DocsImportDialog.vue";
import { useImportResult, viewDraftsHref } from "./docsImport";

const open = ref(false);
const { result, refresh } = useImportResult(5000);

const runningLine = computed(() => {
  const run = result.value;
  if (run?.state !== "running") return "";
  return run.stage === "reading"
    ? __("Importing from {0}, {1} of {2} pages…", [
        run.host,
        run.done + 1,
        run.total,
      ])
    : __("Importing from {0}…", [run.host]);
});

const doneLine = computed(() => {
  const run = result.value;
  if (run?.state !== "done") return "";
  return run.created
    ? __("Last import from {0}: {1} drafts added", [run.host, run.created])
    : __("Last import from {0}: nothing new", [run.host]);
});

onMounted(refresh);
// The dialog may have finished or started a run while closed.
watch(open, (isOpen) => !isOpen && refresh());
</script>
