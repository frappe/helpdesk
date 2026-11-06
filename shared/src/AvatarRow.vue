<template>
  <FileUploader
    :key="uploaderKey"
    :fileTypes="['image/*']"
    v-bind="uploadOptions"
    @success="(file) => emit('upload', file.file_url)"
    @failure="onUploadFailure"
  >
    <template #default="{ openFileSelector, uploading }">
      <div class="flex items-center gap-4">
        <div class="group relative flex-shrink-0 size-16">
          <Avatar
            class="!size-16"
            :image="image"
            :label="name"
            :shape="shape"
          />
          <slot name="badge" />
          <template v-if="editable">
            <!-- one Tooltip each: it wires only its first child -->
            <Tooltip :hoverDelay="0" side="bottom" :text="uploadTooltip">
              <button
                type="button"
                class="z-1 absolute top-0 left-0 cursor-pointer !size-16"
                :class="roundedClass"
                :aria-label="uploadTooltip"
                @click.stop="openFileSelector"
              />
            </Tooltip>
            <Tooltip
              v-if="image"
              :hoverDelay="0"
              side="bottom"
              :text="__('Remove Photo')"
            >
              <button
                type="button"
                :aria-label="__('Remove Photo')"
                class="z-1 size-4 absolute -top-1 -right-1 flex cursor-pointer items-center justify-center rounded-full bg-surface-base opacity-0 duration-300 ease-in-out group-hover:opacity-100 [@media(hover:none)]:opacity-100 hover:bg-surface-gray-2 outline outline-black-overlay-50"
                @click.stop="emit('remove')"
              >
                <LucideX class="size-3.5 text-ink-gray-4" />
              </button>
            </Tooltip>
          </template>
          <div
            v-if="uploading"
            class="w-full h-full top-0 left-0 absolute bg-surface-gray-10 bg-opacity-20 flex items-center justify-center"
            :class="roundedClass"
          >
            <LoadingIndicator class="size-4" />
          </div>
        </div>
        <div class="flex flex-col gap-1">
          <Skeleton
            v-if="!name"
            class="h-3 w-32 rounded-full motion-reduce:animate-none"
          />
          <div v-else-if="!editName" class="flex items-end gap-1">
            <span class="text-md sm:text-xl !font-semibold text-ink-gray-8">
              {{ name }}
            </span>
            <Button
              v-if="editable && renameable"
              class="!px-1 !h-5"
              variant="ghost"
              :aria-label="__('Edit name')"
              @click="editFullName"
            >
              <EditIcon class="size-3.5" />
            </Button>
          </div>
          <div v-else class="flex items-center gap-1">
            <TextInput
              ref="fullNameRef"
              v-model="fullName"
              @keydown.enter="isNameDirty ? save() : (editName = false)"
              @keydown.esc.stop="editName = false"
            />
            <Button
              variant="outline"
              icon="lucide-check"
              :aria-label="__('Save name')"
              :loading="busy"
              :disabled="busy"
              @click="isNameDirty ? save() : (editName = false)"
            />
          </div>
          <span class="text-p-sm text-ink-gray-6">{{ subtitle }}</span>
          <slot />
        </div>
      </div>
    </template>
  </FileUploader>
</template>

<script setup lang="ts">
import LucideX from "~icons/lucide/x";
import EditIcon from "~icons/lucide/edit";
import {
  Avatar,
  Button,
  FileUploader,
  LoadingIndicator,
  Skeleton,
  TextInput,
  Tooltip,
  toast,
} from "frappe-ui";
import { computed, nextTick, ref, useTemplateRef, watch } from "vue";
import { __ } from "./translation";

const props = withDefaults(
  defineProps<{
    name?: string;
    subtitle?: string;
    image?: string;
    shape?: "circle" | "square";
    busy?: boolean;
    editable?: boolean;
    renameable?: boolean;
    uploadOptions?: Record<string, unknown>;
  }>(),
  { shape: "circle", editable: true, renameable: true }
);

const emit = defineEmits<{
  (e: "upload", fileUrl: string): void;
  (e: "remove"): void;
  (e: "rename", fullName: string): void;
}>();

const uploadTooltip = computed(() =>
  props.image ? __("Change Photo") : __("Upload Photo")
);
const roundedClass = computed(() =>
  props.shape === "square" ? "rounded-5" : "rounded-full"
);

const editName = ref(false);
const fullName = ref("");
const fullNameRef = useTemplateRef("fullNameRef");
const isNameDirty = computed(
  () => !!fullName.value.trim() && fullName.value.trim() !== props.name
);

// A saved rename comes back as a new name; a failed one stays open to retry.
watch(
  () => props.name,
  () => (editName.value = false)
);

function editFullName() {
  fullName.value = props.name ?? "";
  editName.value = true;
  nextTick(() => fullNameRef.value?.focus());
}

function save() {
  emit("rename", fullName.value.trim());
}

// FileUploader keeps the failed file in its input, so picking it again fires no change. Remount for a fresh input.
const uploaderKey = ref(0);
function onUploadFailure() {
  toast.error(__("Could not upload the image"));
  uploaderKey.value++;
}
</script>
