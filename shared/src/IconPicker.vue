<template>
  <Popover
    v-model:open="open"
    align="start"
    :trigger="field ? 'manual' : 'click'"
    :auto-focus="!field"
  >
    <template #trigger>
      <TextInput
        v-if="field"
        v-model="fieldValue"
        class="w-full [&_input:focus]:bg-surface-gray-2 [&_input:focus]:ring-2 [&_input:focus]:ring-outline-gray-3"
        autocomplete="off"
        :placeholder="fieldPlaceholder"
        :aria-label="__('Choose an icon')"
        @focus="open = true"
        @click="open = true"
        @keydown.delete="clearIcon"
      >
        <template #prefix>
          <Icon :icon="icon || 'lucide-circle-dashed'" class="size-4" />
        </template>
        <template #suffix>
          <span class="lucide-chevron-down size-4 text-ink-gray-5" />
        </template>
      </TextInput>
      <Button
        v-else
        variant="subtle"
        size="md"
        :aria-label="__('Choose an icon')"
        class="shrink-0"
      >
        <template #icon>
          <CategoryIcon :icon="icon" class="size-4" />
        </template>
      </Button>
    </template>
    <template #default>
      <div
        class="w-[19.5rem] max-w-[calc(100vw-2rem)] px-2 pt-2"
        :class="uploads ? 'pb-1.5' : 'pb-2'"
      >
        <TextInput
          v-if="!field"
          v-model="query"
          v-focus
          :placeholder="__('Search icons')"
          :aria-label="__('Search icons')"
        />
        <div
          class="-mx-2 max-h-72 overflow-y-auto px-2"
          :class="{ 'mt-2.5': !field }"
        >
          <template v-if="uploads && (!search || customMatches.length)">
            <div class="flex h-5 items-center">
              <p class="text-xs text-ink-gray-5">{{ __("Custom") }}</p>
            </div>
            <div :class="[GRID, 'mb-2.5 mt-1.5']">
              <FileUploader
                v-if="!search && uploadEndpoint"
                :file-types="['.png', '.jpg', '.jpeg', '.svg']"
                :private="false"
                :upload-endpoint="uploadEndpoint"
                @success="(file) => uploaded(file.file_url)"
              >
                <template #default="{ uploading, openFileSelector }">
                  <Tooltip :text="__('Upload an icon')">
                    <Button
                      size="md"
                      variant="ghost"
                      icon="lucide-plus"
                      class="border border-dashed border-outline-gray-3"
                      :loading="uploading"
                      :aria-label="__('Upload an icon')"
                      @click="openFileSelector"
                    />
                  </Tooltip>
                </template>
              </FileUploader>
              <div
                v-for="upload in customMatches"
                :key="upload.url"
                class="group relative"
              >
                <Button
                  size="md"
                  :variant="isPicked(upload.url) ? 'subtle' : 'ghost'"
                  :aria-label="uploadLabel(upload)"
                  :aria-pressed="isPicked(upload.url)"
                  @click="pick(upload.url)"
                >
                  <template #icon>
                    <CategoryIcon :icon="upload.url" class="size-4" />
                  </template>
                </Button>
                <Button
                  variant="solid"
                  size="xs"
                  icon="lucide-x"
                  :aria-label="__('Delete {0}', [uploadLabel(upload)])"
                  :loading="deleting === upload.url"
                  class="absolute -right-1 -top-1 !size-4 rounded-full !p-0 shadow-sm transition-opacity focus-visible:opacity-100 group-hover:opacity-100 [&_.lucide-x]:!size-2.5"
                  :class="deleting === upload.url ? 'opacity-100' : 'opacity-0'"
                  @click="emit('delete', upload.url)"
                />
              </div>
            </div>
          </template>
          <template v-if="matches.length">
            <div v-if="uploads" class="flex h-5 items-center">
              <p class="text-xs text-ink-gray-5">{{ __("Icons") }}</p>
            </div>
            <div :class="[GRID, { 'mt-1.5': uploads }]">
              <Button
                v-for="value in matches"
                :key="value"
                size="md"
                :icon="value"
                :variant="value === icon ? 'subtle' : 'ghost'"
                :title="iconLabel(value)"
                :aria-label="iconLabel(value)"
                :aria-pressed="value === icon"
                @click="pick(value)"
              />
            </div>
          </template>
          <p v-if="nothing" class="py-4 text-p-sm text-ink-gray-5">
            {{ __("No icons found") }}
          </p>
        </div>
        <p
          v-if="uploads"
          class="mt-2 border-t border-outline-gray-1 pt-1.5 text-xs text-ink-gray-5"
        >
          {{ __("Square SVG or PNG, at least 64 px.") }}
        </p>
      </div>
    </template>
  </Popover>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import {
  Button,
  FileUploader,
  Popover,
  TextInput,
  Tooltip,
  vFocus,
} from "frappe-ui";
import { CATEGORY_ICONS, type UploadedIcon } from "./categoryIcons";
import CategoryIcon from "./CategoryIcon.vue";
import Icon from "./Icon.vue";
import { __ } from "./translation";

// `field` shows a full-width input that searches as you type.
const props = defineProps<{
  field?: boolean;
  placeholder?: string;
  uploads?: UploadedIcon[];
  uploadEndpoint?: string;
  deleting?: string;
}>();

const icon = defineModel<string>();
const emit = defineEmits<{ upload: [url: string]; delete: [url: string] }>();
const open = ref(false);
const query = ref("");
const GRID = "grid grid-cols-[repeat(8,2rem)] justify-between gap-y-1";

const iconLabel = (value: string) =>
  value.replace("lucide-", "").replace(/-/g, " ");
const iconTitle = (value?: string) =>
  iconLabel(value || "").replace(/\b\w/g, (char) => char.toUpperCase());
const fieldPlaceholder = computed(
  () => iconTitle(icon.value) || props.placeholder || __("Select an icon...")
);
const fieldValue = computed({
  get: () => (open.value ? query.value : iconTitle(icon.value)),
  set: (value: string) => {
    query.value = value;
    open.value = true;
  },
});
const search = computed(() => query.value.trim().toLowerCase());
const matches = computed(() =>
  CATEGORY_ICONS.filter((value) => iconLabel(value).includes(search.value))
);
const customMatches = computed(() =>
  (props.uploads || [])
    .map((upload, index) => ({ ...upload, index }))
    .filter(
      (upload) =>
        !search.value ||
        upload.used_by.some((name) => name.toLowerCase().includes(search.value))
    )
);
const nothing = computed(
  () => !matches.value.length && !customMatches.value.length
);

const isPicked = (url: string) => url === icon.value;
const uploadLabel = (upload: { index: number }) =>
  __("Uploaded icon {0}", [upload.index + 1]);

watch(open, () => (query.value = ""));

// Deleting past an empty search clears the icon.
function clearIcon() {
  if (!query.value) icon.value = "";
}

function uploaded(url: string) {
  emit("upload", url);
  pick(url);
}

function pick(value: string) {
  icon.value = value;
  open.value = false;
}
</script>
