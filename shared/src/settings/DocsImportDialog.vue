<template>
  <Dialog
    v-model:open="open"
    :title="__('Import existing knowledge base')"
    size="md"
  >
    <div class="space-y-5">
      <!-- Form and error share the fields; the error adds its message above the button -->
      <template v-if="screen === 'form' || screen === 'error'">
        <div class="space-y-4" @keydown.enter="onEnter">
          <TextInput
            v-model="url"
            :label="__('Docs site address')"
            placeholder="https://docs.example.com"
            type="url"
            maxlength="500"
            required
            autofocus
          />
          <Combobox
            v-model="category"
            :label="__('Add the drafts to')"
            :placeholder="__('Pick a category')"
            :options="options"
            :loading="categories.loading"
            :description="
              noCategories
                ? __('No categories yet. Create one first.')
                : undefined
            "
            required
          />
        </div>
        <p
          v-if="errorText"
          class="flex items-start gap-2 text-p-sm text-ink-red-6"
          role="alert"
        >
          <LucideCircleAlert
            class="mt-0.5 size-4 shrink-0"
            aria-hidden="true"
          />
          {{ errorText }}
        </p>
        <div class="flex items-center gap-4">
          <p class="min-w-0 flex-1 text-p-sm text-ink-gray-5">
            {{
              pageLimit.data
                ? __(
                    "Up to {0} new pages per import. Pages you have already imported are skipped.",
                    [pageLimit.data]
                  )
                : __("Pages you have already imported are skipped.")
            }}
          </p>
          <Button
            variant="solid"
            :label="screen === 'error' ? __('Try again') : __('Import')"
            :disabled="screen !== 'error' && !canImport"
            :loading="start.loading"
            @click="screen === 'error' ? (showForm = true) : submit()"
          />
        </div>
      </template>

      <template v-else-if="screen === 'working' && run?.state === 'running'">
        <div class="space-y-3" aria-live="polite">
          <p class="flex items-center gap-2 text-base text-ink-gray-8">
            <LucideLoaderCircle
              class="size-4 shrink-0 animate-spin text-ink-gray-6 motion-reduce:animate-none"
              aria-hidden="true"
            />
            <span class="min-w-0 truncate" :title="run.host">{{
              stepText
            }}</span>
          </p>
        </div>
        <p class="text-p-sm text-ink-gray-5">
          {{
            timedOut
              ? __(
                  "This is taking longer than expected. Check back in a few minutes."
                )
              : __("You can close this window. The import keeps running.")
          }}
        </p>
        <div class="flex justify-end">
          <Button variant="ghost" :label="__('Close')" @click="open = false" />
        </div>
      </template>

      <template v-else-if="screen === 'done' && run?.state === 'done'">
        <DocsImportSummary :result="run" :category-label="categoryLabel" />
        <div class="flex justify-end gap-2">
          <Button
            variant="ghost"
            :label="__('Import another')"
            @click="anotherImport"
          />
          <Button
            v-if="nothingNew"
            variant="solid"
            :label="__('Close')"
            @click="open = false"
          />
          <Button
            v-else
            variant="solid"
            :label="__('View drafts')"
            :href="viewDraftsHref(run.category)"
          />
        </div>
      </template>
    </div>
  </Dialog>
</template>

<script setup lang="ts">
import { Button, Combobox, Dialog, TextInput, createResource } from "frappe-ui";
import { computed, ref, watch } from "vue";
import LucideCircleAlert from "~icons/lucide/circle-alert";
import LucideLoaderCircle from "~icons/lucide/loader-circle";
import { __ } from "../translation";
import DocsImportSummary from "./DocsImportSummary.vue";
import {
  type ImportResult,
  siteCategoryName,
  useImportResult,
  viewDraftsHref,
} from "./docsImport";

// Picker value for "create a category named after the site".
const NEW_CATEGORY = ":new-category";

const open = defineModel<boolean>("open", { required: true });
const emit = defineEmits<{ started: [] }>();

const url = ref("");
const category = ref("");
// "Import another" and "Try again" show the form over the last result.
const showForm = ref(false);
const { result: run, timedOut, refresh, stop } = useImportResult(2000);

const categories = createResource({
  url: "helpdesk.api.knowledge_base.get_category_options",
});

const pageLimit = createResource({
  url: "helpdesk.api.docs_source.get_page_limit",
  method: "GET",
  cache: "docs-import-page-limit",
});

// Fixed copy: a failed call must never show the server's own text.
const start = createResource({
  url: "helpdesk.api.docs_source.import_docs",
  onSuccess(state: ImportResult) {
    run.value = state;
    showForm.value = false;
    if (state.state === "running") {
      emit("started");
      refresh();
    }
    // A new category has to show up in the picker and in the result.
    if (category.value === NEW_CATEGORY) categories.reload();
  },
  onError(error: { exc_type?: string }) {
    const message =
      error?.exc_type === "PermissionError"
        ? __("Only Agent Managers can import pages.")
        : __(
            "We couldn't start the import. Check your connection and try again."
          );
    run.value = { state: "error", message, host: "" };
    showForm.value = false;
  },
});

const newCategoryName = computed(() => siteCategoryName(url.value.trim()));

// Offered first, unless a category of that name already exists.
const options = computed(() => {
  const existing = (categories.data || []).map(({ value, label }) => ({
    value,
    label,
  }));
  const name = newCategoryName.value;
  const taken = existing.some(
    (o) => o.label.toLowerCase() === name.toLowerCase()
  );
  if (!name || taken) return existing;
  const label = __("New category: {0}", [name]);
  return [{ value: NEW_CATEGORY, label }, ...existing];
});
const noCategories = computed(
  () => categories.data && !options.value.length && !categories.loading
);
const canImport = computed(
  () =>
    Boolean(url.value.trim() && category.value) &&
    (category.value !== NEW_CATEGORY || Boolean(newCategoryName.value)) &&
    !start.loading
);

const screen = computed(() => {
  if (showForm.value) return "form";
  const state = run.value?.state;
  return state === "running" ? "working" : state || "form";
});

const errorText = computed(() => {
  if (categories.error)
    return __("Couldn't load the categories. Close this window and try again.");
  const state = run.value;
  return screen.value === "error" && state?.state === "error"
    ? state.message
    : "";
});

const stepText = computed(() => {
  const state = run.value;
  if (state?.state !== "running") return "";
  if (state.stage === "reading")
    return state.done === 1
      ? __("Read 1 page on {0}…", [state.host])
      : __("Read {0} pages on {1}…", [state.done, state.host]);
  // Queued, no worker has picked it up yet.
  if (state.stage === "waiting") return __("Waiting to start…");
  return __("Looking for pages on {0}…", [state.host]);
});

const nothingNew = computed(
  () => run.value?.state === "done" && !run.value.created && !run.value.failed
);

const categoryLabel = computed(() => {
  const state = run.value;
  if (state?.state !== "done") return "";
  return options.value.find((o) => o.value === state.category)?.label || "";
});

watch(open, (isOpen) => {
  if (!isOpen) return stop();
  showForm.value = false;
  categories.submit();
  pageLimit.fetch();
  refresh();
});

function anotherImport() {
  category.value = "";
  showForm.value = true;
}

// Enter on the category list picks an option; it must not start the import.
function onEnter(event: KeyboardEvent) {
  if ((event.target as HTMLElement).getAttribute("role") !== "combobox")
    submit();
}

function submit() {
  if (!canImport.value) return;
  const target =
    category.value === NEW_CATEGORY
      ? { new_category: newCategoryName.value }
      : { category: category.value };
  start.submit({ url: url.value.trim(), ...target });
}
</script>
