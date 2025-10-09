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
        v-if="!props.image"
        :fileTypes="['image/*']"
        @success="
          (file) => {
            emit('onUpload', file.file_url);
          }
        "
      >
        <template #default="{ openFileSelector }">
          <Button
            @click="openFileSelector()"
            iconLeft="upload"
            label="Upload Image"
            :loading="props.isLoading"
            :disabled="props.isDisabled"
          />
        </template>
      </FileUploader>

      <div v-else>
        <Button
          :label="`Remove ${props.title}`"
          @click="emit('onRemove')"
          iconLeft="trash"
          theme="red"
          :loading="props.isLoading"
          :disabled="props.isDisabled"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Avatar, Button, FeatherIcon, FileUploader } from "frappe-ui";

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
  isDisabled: {
    type: Boolean,
    required: true,
  },
});
</script>
