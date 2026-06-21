<template>
  <div class="flex items-center gap-4">
    <FileUploader :fileTypes="['image/*']" @success="onSuccess">
      <template #default="{ openFileSelector, uploading }">
        <!-- Filled: image with hover-to-replace + remove badge -->
        <div v-if="image" class="group relative size-11.5 shrink-0">
          <Avatar
            :image="image"
            :label="fallbackLabel"
            :shape="shape"
            size="3xl"
          />
          <button
            type="button"
            class="absolute inset-0 flex cursor-pointer items-center justify-center bg-black/40 text-white opacity-0 outline-none transition focus:outline-none focus-visible:outline-none group-hover:opacity-100"
            :class="roundedClass"
            :aria-label="__('Replace image')"
            @click.prevent="openFileSelector()"
          >
            <LucidePencil class="size-4" />
          </button>
          <button
            type="button"
            class="absolute -right-2.5 -top-2.5 flex size-4.5 cursor-pointer items-center justify-center rounded-full bg-surface-white text-ink-gray-4 opacity-0 outline outline-black-overlay-50 duration-300 ease-in-out focus:outline-none focus-visible:outline-none hover:bg-surface-gray-2 group-hover:opacity-100"
            :aria-label="__('Remove image')"
            @click.prevent="image = ''"
          >
            <LucideX class="size-2.5" />
          </button>
        </div>

        <!-- Empty: upload box -->
        <button
          v-else
          type="button"
          class="flex size-11.5 shrink-0 cursor-pointer items-center justify-center border border-outline-gray-2 text-ink-gray-4 outline-none transition focus:outline-none focus-visible:outline-none hover:border-outline-gray-3"
          :class="roundedClass"
          :disabled="uploading"
          :aria-label="label || __('Upload image')"
          @click.prevent="openFileSelector()"
        >
          <LucideUpload class="size-4.5" />
        </button>
      </template>
    </FileUploader>

    <div v-if="label || description" class="flex flex-col gap-0.5">
      <span v-if="label" class="text-p-sm font-medium text-ink-gray-8">
        {{ __(label) }}
      </span>
      <span v-if="description" class="text-p-sm text-ink-gray-5">
        {{ __(description) }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import type { File as FileType } from "@/types";
import { Avatar, FileUploader } from "frappe-ui";
import { computed } from "vue";
import LucidePencil from "~icons/lucide/pencil";
import LucideUpload from "~icons/lucide/upload";
import LucideX from "~icons/lucide/x";

const image = defineModel<string>({ default: "" });

const props = withDefaults(
  defineProps<{
    label?: string;
    description?: string;
    fallbackLabel?: string;
    shape?: "circle" | "square";
  }>(),
  {
    label: "",
    description: __("Upload an image in PNG or JPG format"),
    fallbackLabel: "",
    shape: "square",
  }
);

const roundedClass = computed(() =>
  props.shape === "circle" ? "rounded-full" : "rounded-[10px]"
);

function onSuccess(file: FileType) {
  image.value = file.file_url;
}
</script>
