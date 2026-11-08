<template>
  <Dialog
    v-model:open="open"
    :title="__('Import pages from a docs site')"
    size="md"
  >
    <template #default>
      <div class="space-y-5">
        <!-- Form and error share the fields; the error adds its message above them -->
        <template v-if="screen === 'form' || screen === 'error'">
          <p
            v-if="errorText"
            class="flex items-start gap-2 text-p-sm text-ink-red-3"
            role="alert"
          >
            <LucideCircleAlert
              class="mt-0.5 size-4 shrink-0"
              aria-hidden="true"
            />
            {{ errorText }}
          </p>
          <div class="space-y-4" @keydown.enter="onEnter">
            <TextInput
              v-model="url"
              :label="__('Docs site address')"
              :description="
                __('We look for an llms.txt first, then a sitemap.xml.')
              "
              :placeholder="'https://docs.example.com'"
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
          <p class="text-p-sm text-ink-gray-5">
            {{ __("Pages you have already imported are skipped.") }}
          </p>
          <div class="flex justify-end">
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
            <p
              v-if="run.stage !== 'reading'"
              class="flex items-center gap-2 text-base text-ink-gray-8"
            >
              <LucideLoaderCircle
                class="size-4 shrink-0 animate-spin text-ink-gray-6 motion-reduce:animate-none"
                aria-hidden="true"
              />
              <span class="min-w-0 truncate" :title="run.host">{{
                stepText
              }}</span>
            </p>
            <Progress v-else :value="percent" :label="stepText" hint />
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
            <Button
              variant="ghost"
              :label="__('Close')"
              @click="open = false"
            />
          </div>
        </template>

        <template v-else-if="screen === 'done' && run?.state === 'done'">
          <p
            v-if="nothingNew"
            class="flex items-start gap-3 text-p-base text-ink-gray-8"
          >
            <LucideCircleCheck
              class="mt-0.5 size-5 shrink-0 text-ink-gray-6"
              aria-hidden="true"
            />
            {{ __("Everything on {0} is already imported.", [run.host]) }}
          </p>
          <template v-else>
            <dl
              class="grid grid-cols-3 divide-x divide-outline-gray-2 rounded-5 border border-outline-gray-2"
            >
              <div
                v-for="figure in figures"
                :key="figure.label"
                class="px-3 py-4"
              >
                <dd class="text-3xl tabular-nums text-ink-gray-9">
                  {{ figure.value }}
                </dd>
                <dt class="mt-1 text-p-sm text-ink-gray-5">
                  {{ figure.label }}
                </dt>
              </div>
            </dl>
          </template>
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
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import {
  Button,
  Combobox,
  Dialog,
  Progress,
  TextInput,
  createResource,
} from "frappe-ui";
import { computed, ref, watch } from "vue";
import LucideCircleAlert from "~icons/lucide/circle-alert";
import LucideCircleCheck from "~icons/lucide/circle-check";
import LucideLoaderCircle from "~icons/lucide/loader-circle";
import { __ } from "../translation";
import {
  type ImportResult,
  useImportResult,
  viewDraftsHref,
} from "./docsImport";

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

const options = computed(() =>
  (categories.data || []).map(({ value, label }) => ({ value, label }))
);
const noCategories = computed(
  () => categories.data && !categories.data.length && !categories.loading
);
const canImport = computed(
  () => Boolean(url.value.trim() && category.value) && !start.loading
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

const percent = computed(() => {
  const state = run.value;
  if (state?.state !== "running" || !state.total) return 0;
  return Math.round((state.done / state.total) * 100);
});

const stepText = computed(() => {
  const state = run.value;
  if (state?.state !== "running") return "";
  if (state.stage === "reading")
    return __("Reading page {0} of {1}", [state.done + 1, state.total]);
  return __("Looking for pages on {0}…", [state.host]);
});

const nothingNew = computed(
  () => run.value?.state === "done" && !run.value.created && !run.value.failed
);

const figures = computed(() => {
  const state = run.value;
  if (state?.state !== "done") return [];
  return [
    { label: __("Added"), value: state.created },
    { label: __("Already imported"), value: state.skipped },
    { label: __("Couldn't read"), value: state.failed },
  ];
});

watch(open, (isOpen) => {
  if (!isOpen) return stop();
  showForm.value = false;
  categories.submit();
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
  if (canImport.value)
    start.submit({ url: url.value.trim(), category: category.value });
}
</script>
