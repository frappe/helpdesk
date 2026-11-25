<template>
  <section class="flex flex-col gap-4">
    <div class="flex items-start justify-between gap-4">
      <div class="flex min-w-0 flex-col gap-1">
        <span class="text-base-semibold text-ink-gray-9">
          {{ __("Knowledge sources") }}
        </span>
        <span class="text-p-sm text-ink-gray-6">
          {{
            __(
              "Published articles are always included and keep their own visibility. Add documentation sites or files too."
            )
          }}
        </span>
      </div>
      <Button
        class="shrink-0"
        :label="__('Add source')"
        icon-left="lucide-plus"
        @click="showAdd = true"
      />
    </div>

    <div
      v-if="sources.data?.length"
      class="divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-1"
    >
      <div
        v-for="source in sources.data"
        :key="source.name"
        class="flex flex-col gap-2 px-4 py-3 sm:flex-row sm:items-center sm:gap-4"
      >
        <div class="flex min-w-0 flex-1 items-start gap-3">
          <LucideGlobe
            v-if="source.source_type === 'URL'"
            class="mt-0.5 size-4 shrink-0 text-ink-gray-5"
          />
          <LucideFileText
            v-else
            class="mt-0.5 size-4 shrink-0 text-ink-gray-5"
          />
          <div class="flex min-w-0 flex-col gap-0.5">
            <span
              class="truncate text-base-medium text-ink-gray-8"
              :title="source.title"
            >
              {{ source.title }}
            </span>
            <span
              v-if="source.status === 'Failed'"
              class="text-p-sm text-ink-red-4"
            >
              {{ source.error }}
            </span>
          </div>
        </div>
        <div class="flex shrink-0 items-center justify-between gap-2 pl-7 sm:pl-0">
          <Select
            class="w-32"
            :model-value="source.visibility"
            :options="VISIBILITY_OPTIONS"
            :aria-label="__('Visible to')"
            @update:model-value="setVisibility(source, $event)"
          />
          <div class="flex items-center gap-2">
            <Badge
              :label="__(source.status)"
              :theme="source.status === 'Failed' ? 'red' : 'gray'"
              variant="subtle"
            />
            <Dropdown :options="rowActions(source)" align="end">
              <Button
                variant="ghost"
                icon="lucide-ellipsis"
                :aria-label="__('More actions')"
              />
            </Dropdown>
          </div>
        </div>
      </div>
    </div>
    <div
      v-else-if="sources.data"
      class="flex flex-col items-center gap-2 rounded-lg border border-dashed border-outline-gray-2 px-4 py-8 text-center"
    >
      <LucideLibrary class="size-5 text-ink-gray-5" />
      <span class="text-base text-ink-gray-7">
        {{ __("No extra sources yet") }}
      </span>
      <span class="text-p-sm text-ink-gray-5">
        {{ __("Add a documentation site or a PDF, MD or TXT file.") }}
      </span>
    </div>

    <Dialog v-model:open="showAdd" :title="__('Add knowledge source')">
      <template #default>
        <div class="flex flex-col gap-4">
          <TabButtons v-model="form.type" :options="TYPE_OPTIONS" />
          <FormControl
            v-if="form.type === 'URL'"
            v-model="form.url"
            :label="__('Documentation link')"
            placeholder="https://docs.example.com"
          />
          <FileUploader
            v-else
            :file-types="FILE_TYPES"
            :private="true"
            @success="(file) => (form.file = file)"
          >
            <template #default="{ uploading, progress, openFileSelector }">
              <div class="flex flex-col gap-1.5">
                <span class="text-xs text-ink-gray-5">{{ __("File") }}</span>
                <button
                  type="button"
                  class="flex w-full flex-col items-center gap-1.5 rounded-lg border border-dashed border-outline-gray-3 px-4 py-6 text-center hover:bg-surface-gray-1 focus-visible:outline focus-visible:outline-outline-gray-3"
                  @click="openFileSelector"
                >
                  <LucideUpload class="size-5 text-ink-gray-5" />
                  <span class="text-base text-ink-gray-8">
                    {{
                      uploading
                        ? __("Uploading {0}%", [progress])
                        : form.file?.file_name || __("Choose a file")
                    }}
                  </span>
                  <span class="text-p-sm text-ink-gray-5">
                    {{ __("PDF, MD or TXT") }}
                  </span>
                </button>
              </div>
            </template>
          </FileUploader>
          <FormControl
            v-model="form.visibility"
            type="select"
            :label="__('Visible to')"
            :options="VISIBILITY_HINTS"
          />
          <ErrorMessage :message="add.error?.messages?.[0]" />
        </div>
      </template>
      <template #actions>
        <div class="flex justify-end gap-2">
          <Button :label="__('Cancel')" @click="showAdd = false" />
          <Button
            variant="solid"
            :label="__('Add source')"
            :loading="add.loading"
            @click="add.submit()"
          />
        </div>
      </template>
    </Dialog>

    <Dialog
      :open="Boolean(removing)"
      :title="__('Remove source')"
      :message="
        __('Search will stop using {0}. You can add it again later.', [
          removing?.title,
        ])
      "
      icon="lucide-trash-2"
      theme="red"
      :actions="[
        { label: __('Cancel'), onClick: ({ close }) => close() },
        {
          label: __('Remove'),
          variant: 'solid',
          theme: 'red',
          onClick: ({ close }) => remove.submit().then(close),
        },
      ]"
      @update:open="(open) => !open && (removing = null)"
    />
  </section>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import {
  Badge,
  Button,
  createResource,
  Dialog,
  Dropdown,
  ErrorMessage,
  FileUploader,
  FormControl,
  Select,
  TabButtons,
  toast,
} from "frappe-ui";
import { reactive, ref, watch } from "vue";
import LucideFileText from "~icons/lucide/file-text";
import LucideGlobe from "~icons/lucide/globe";
import LucideLibrary from "~icons/lucide/library";
import LucideUpload from "~icons/lucide/upload";

type Source = {
  name: string;
  title: string;
  source_type: "URL" | "File";
  visibility: string;
  status: "Syncing" | "Ready" | "Failed";
  error: string | null;
};

const API = "helpdesk.api.ai_search";
const FILE_TYPES = [".pdf", ".md", ".txt"];
const TYPE_OPTIONS = [
  { label: __("Website"), value: "URL" },
  { label: __("File"), value: "File" },
];
const VISIBILITY_OPTIONS = [
  { label: __("Public"), value: "Public" },
  { label: __("Customers"), value: "Customers" },
  { label: __("Agents"), value: "Agents" },
];
const VISIBILITY_HINTS = [
  { label: __("Public: everyone, including guests"), value: "Public" },
  { label: __("Customers: signed-in customers and agents"), value: "Customers" },
  { label: __("Agents: agents only"), value: "Agents" },
];
const POLL_MS = 5000;

const sources = createResource({ url: `${API}.get_sources`, auto: true });

// Sources sync in the background, so check again while any is syncing.
let poll: ReturnType<typeof setTimeout> | undefined;
watch(
  () => sources.data,
  (rows: Source[] | undefined) => {
    clearTimeout(poll);
    if (rows?.some((row) => row.status === "Syncing"))
      poll = setTimeout(() => sources.reload(), POLL_MS);
  }
);

const showAdd = ref(false);
const form = reactive({
  type: "URL",
  url: "",
  file: null as { file_url: string; file_name: string } | null,
  visibility: "Public",
});
watch(showAdd, (open) => {
  if (!open) return;
  Object.assign(form, { type: "URL", url: "", file: null, visibility: "Public" });
  add.reset();
});

const add = createResource({
  url: `${API}.add_source`,
  makeParams: () => ({
    source_type: form.type,
    url: form.type === "URL" ? form.url : undefined,
    file_url: form.type === "File" ? form.file?.file_url : undefined,
    visibility: form.visibility,
  }),
  onSuccess() {
    showAdd.value = false;
    sources.reload();
    toast.success(__("Source added. Syncing now."));
  },
});

function showError(error: { messages?: string[] }) {
  toast.error(error.messages?.[0] || __("Something went wrong"));
}

const move = createResource({
  url: `${API}.set_source_visibility`,
  onSuccess: () => sources.reload(),
  onError: showError,
});
function setVisibility(source: Source, visibility: string) {
  move.submit({ name: source.name, visibility });
}

const resync = createResource({
  url: `${API}.resync_source`,
  onSuccess: () => sources.reload(),
  onError: showError,
});

const removing = ref<Source | null>(null);
const remove = createResource({
  url: `${API}.remove_source`,
  makeParams: () => ({ name: removing.value?.name }),
  onSuccess: () => sources.reload(),
  onError: showError,
});

function rowActions(source: Source) {
  return [
    {
      label: __("Sync again"),
      icon: "lucide-refresh-cw",
      onClick: () => resync.submit({ name: source.name }),
    },
    {
      label: __("Remove"),
      icon: "lucide-trash-2",
      onClick: () => (removing.value = source),
    },
  ];
}
</script>
