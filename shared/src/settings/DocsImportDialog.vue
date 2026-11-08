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
          <Alert
            v-if="message"
            theme="red"
            :title="__('Couldn’t import pages')"
            :description="message"
            role="alert"
          />
          <div class="space-y-4" @keydown.enter="submit">
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
            <p
              v-if="categories.error"
              class="flex items-start gap-2 text-p-sm text-ink-red-5"
              role="alert"
            >
              <span
                class="lucide-circle-alert mt-0.5 size-4 shrink-0"
                aria-hidden="true"
              />
              {{
                __(
                  "Couldn't load the categories. Close this window and try again."
                )
              }}
            </p>
            <Combobox
              v-else
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
              :loading="starting"
              @click="screen === 'error' ? tryAgain() : submit()"
            />
          </div>
        </template>

        <template v-else-if="screen === 'working' && run?.state === 'running'">
          <div class="space-y-3" aria-live="polite">
            <p
              v-if="run.stage !== 'reading'"
              class="flex items-center gap-2 text-base text-ink-gray-8"
            >
              <span
                class="lucide-loader-circle size-4 shrink-0 animate-spin text-ink-gray-6 motion-reduce:animate-none"
                aria-hidden="true"
              />
              <span class="min-w-0 truncate" :title="run.host">{{
                stepText
              }}</span>
            </p>
            <template v-else>
              <Progress :value="percent" :label="stepText" hint />
              <p class="truncate text-p-sm text-ink-gray-5" :title="run.host">
                {{ __("From {0}", [run.host]) }}
              </p>
            </template>
          </div>
          <p class="text-p-sm text-ink-gray-5">
            {{
              timedOut
                ? slowCopy()
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

        <template v-else-if="screen === 'nothing-new' && run?.state === 'done'">
          <div class="flex items-start gap-3">
            <span
              class="lucide-circle-check mt-0.5 size-5 shrink-0 text-ink-gray-6"
              aria-hidden="true"
            />
            <p class="text-p-base text-ink-gray-8">
              {{ __("Everything on {0} is already imported.", [run.host]) }}
            </p>
          </div>
          <div class="flex justify-end gap-2">
            <Button
              variant="ghost"
              :label="__('Import another')"
              @click="anotherImport"
            />
            <Button
              variant="solid"
              :label="__('Close')"
              @click="open = false"
            />
          </div>
        </template>

        <template v-else-if="screen === 'done' && run?.state === 'done'">
          <p class="truncate text-p-sm text-ink-gray-5" :title="run.host">
            {{ __("Finished reading {0}", [run.host]) }}
          </p>
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
              <dt class="mt-1 text-p-sm text-ink-gray-5">{{ figure.label }}</dt>
            </div>
          </dl>
          <div class="flex justify-end gap-2">
            <Button
              variant="ghost"
              :label="__('Import another')"
              @click="anotherImport"
            />
            <Button
              variant="solid"
              :link="viewDraftsHref(run.category)"
              :label="__('View drafts')"
            />
          </div>
        </template>
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import {
  Alert,
  Button,
  Combobox,
  Dialog,
  Progress,
  TextInput,
  call,
  createResource,
} from "frappe-ui";
import { computed, ref, watch } from "vue";
import { __ } from "../translation";
import {
  notAllowed,
  slowCopy,
  startFailed,
  useImportResult,
  viewDraftsHref,
} from "./docsImport";

const open = defineModel<boolean>("open", { required: true });
const emit = defineEmits<{ started: [] }>();

const url = ref("");
const category = ref("");
const starting = ref(false);
const failure = ref("");
// "Import another" and "Try again" go back to the form over the last result.
const wantsForm = ref(false);
const { result: run, timedOut, refresh, stop } = useImportResult(2000);

const categories = createResource({
  url: "helpdesk.api.knowledge_base.get_category_options",
});

const options = computed(() =>
  (categories.data || []).map(({ value, label }) => ({ value, label }))
);
const noCategories = computed(
  () => categories.data && !categories.data.length && !categories.loading
);
const canImport = computed(
  () => Boolean(url.value.trim() && category.value) && !starting.value
);

const screen = computed(() => {
  if (failure.value || wantsForm.value) return failure.value ? "error" : "form";
  const state = run.value?.state;
  if (state === "running") return "working";
  if (state === "error") return "error";
  if (state === "done")
    return run.value.created || run.value.failed ? "done" : "nothing-new";
  return "form";
});

// The stored error is stale once the form is shown again for a new run.
const message = computed(
  () =>
    failure.value ||
    (screen.value === "error" && run.value?.state === "error"
      ? run.value.message
      : "")
);

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
  wantsForm.value = false;
  failure.value = "";
  categories.submit();
  refresh();
});

function tryAgain() {
  wantsForm.value = true;
  failure.value = "";
}

function anotherImport() {
  category.value = "";
  wantsForm.value = true;
}

async function submit() {
  if (!canImport.value) return;
  starting.value = true;
  failure.value = "";
  try {
    run.value = await call("helpdesk.api.docs_source.import_docs", {
      url: url.value.trim(),
      category: category.value,
    });
    wantsForm.value = false;
    if (run.value?.state === "running") {
      emit("started");
      refresh();
    } else {
      // A refusal such as a bad address: shown, with the fields kept.
      failure.value = run.value?.state === "error" ? run.value.message : "";
    }
  } catch (error) {
    failure.value = isDenied(error) ? notAllowed() : startFailed();
  } finally {
    starting.value = false;
  }
}

function isDenied(error: unknown) {
  return (error as { exc_type?: string })?.exc_type === "PermissionError";
}
</script>
