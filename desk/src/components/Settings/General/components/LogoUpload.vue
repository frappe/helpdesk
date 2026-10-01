<template>
  <div
    class="flex flex-col sm:flex-row items-center justify-between gap-4 mt-4 w-full"
  >
    <div class="flex flex-col sm:flex-row items-center gap-3.5">
      <div
        class="flex items-center justify-center min-w-16 min-h-16 rounded-6 overflow-hidden border border-outline-gray-1"
      >
        <!-- Square and full-bleed: these are logos and banners, not people. -->
        <Avatar
          v-if="props.image"
          shape="square"
          class="size-16"
          :image="props.image"
          :label="props.title"
        />
        <LucideImage v-else class="size-6 text-ink-gray-4" />
      </div>
      <div class="flex flex-col gap-1 max-w-sm items-start">
        <span class="text-base-medium text-ink-gray-8">{{ title }}</span>
        <span class="text-p-sm text-ink-gray-6">{{ description }}</span>
      </div>
    </div>
    <div>
      <!-- Public: logos and banners are served to signed-out portal visitors. -->
      <FileUploader
        :fileTypes="['image/*']"
        :private="false"
        @success="
          (file) => {
            emit('onUpload', file.file_url);
          }
        "
      >
        <template v-slot="{ progress, uploading, openFileSelector }">
          <div class="flex items-end gap-x-2">
            <Button
              @click="openFileSelector"
              :iconLeft="ImageUpIcon"
              :label="
                uploading
                  ? __('Uploading {0}%', progress)
                  : props.image
                  ? __('Change')
                  : __('Upload')
              "
              :loading="isLoading"
            />
            <Button
              v-if="props.image"
              iconLeft="lucide-trash-2"
              :label="__('Remove')"
              @click="emit('onRemove')"
              :loading="isLoading"
            />
          </div>
        </template>
      </FileUploader>
    </div>
  </div>
</template>

<script setup lang="ts">
import LucideImage from "~icons/lucide/image";
import { Avatar, Button, FileUploader } from "frappe-ui";
import ImageUpIcon from "~icons/lucide/image-up";

const emit = defineEmits(["onUpload", "onRemove"]);

const props = defineProps({
  title: {
    type: String,
    required: true,
  },
  description: {
    type: String,
    required: true,
  },
  image: {
    type: String,
    required: true,
  },
  isLoading: {
    type: Boolean,
    required: true,
  },
});
</script>
