<template>
  <div
    class="flex flex-col sm:flex-row items-center justify-between gap-4 mt-4 w-full"
  >
    <div class="flex flex-col sm:flex-row items-center gap-3.5">
      <div
        class="flex items-center justify-center min-w-16 min-h-16 rounded-lg overflow-hidden border border-gray-100"
      >
        <Avatar
          v-if="props.image"
          size="3xl"
          :image="props.image"
          :label="props.title"
        />
        <FeatherIcon v-else name="image" class="size-6 text-ink-gray-4" />
      </div>
      <div class="flex flex-col gap-1 max-w-sm items-start">
        <span class="text-base font-medium text-ink-gray-8">{{ title }}</span>
        <span class="text-p-sm text-ink-gray-6">{{ description }}</span>
      </div>
    </div>
    <div>
      <FileUploader
        :fileTypes="['image/*']"
        @success="
          (file) => {
            emit('onUpload', file.file_url);
          }
        "
      >
        <template v-slot="{ progress, uploading, openFileSelector }">
          <div class="flex items-end space-x-2">
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
              iconLeft="trash-2"
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
import { Avatar, Button, FeatherIcon, FileUploader } from "frappe-ui";
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
