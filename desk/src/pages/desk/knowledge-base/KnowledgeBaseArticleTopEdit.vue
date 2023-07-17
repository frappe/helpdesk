<template>
  <div class="mb-7 flex w-max items-center gap-1 rounded bg-gray-100 px-2 py-1">
    <div class="text-base text-gray-600">
      {{ categoryName }}
    </div>
    <IconChevronRight class="h-3 w-3 text-gray-600" />
    <div class="text-base text-gray-800">
      {{ subCategoryName }}
    </div>
  </div>
  <div class="mb-4.5 flex items-center justify-between">
    <div class="flex items-center gap-2">
      <Avatar :label="authorFullname" :image="authorImage" />
      <div class="text-base text-gray-800">
        {{ authorFullname }}
      </div>
    </div>
    <div class="flex items-center gap-2 text-sm text-gray-600">
      <div class="text-gray-600">Created</div>
      <div class="text-gray-800">
        {{ dayjs(creation).fromNow() }}
      </div>
      <div class="text-base text-gray-300">|</div>
      <div class="text-gray-600">Modified</div>
      <div class="text-gray-800">
        {{ dayjs(modified).fromNow() }}
      </div>
      <div class="text-base text-gray-300">|</div>
      <IconThumbsUp class="h-4 w-4" />
      <div class="text-gray-600">Likes</div>
      <div class="text-gray-800">
        {{ likes }}
      </div>
      <div class="text-base text-gray-300">|</div>
      <IconThumbsDown class="h-4 w-4" />
      <div class="text-gray-600">Dislikes</div>
      <div class="text-gray-800">
        {{ dislikes }}
      </div>
    </div>
  </div>
  <div class="border-b pb-3 text-3xl font-semibold text-gray-900">
    {{ title }}
  </div>
</template>

<script setup lang="ts">
import { Avatar } from "frappe-ui";
import dayjs from "dayjs";
import IconChevronRight from "~icons/lucide/chevron-right";
import IconThumbsDown from "~icons/lucide/thumbs-down";
import IconThumbsUp from "~icons/lucide/thumbs-up";

defineProps({
  categoryName: {
    type: String,
    required: true,
  },
  subCategoryName: {
    type: String,
    required: true,
  },
  title: {
    type: String,
    required: true,
  },
  authorFullname: {
    type: String,
    required: true,
  },
  authorImage: {
    type: String,
    required: true,
  },
  creation: {
    type: String,
    required: true,
  },
  modified: {
    type: String,
    required: true,
  },
  likes: {
    type: Number,
    required: false,
    default: 0,
  },
  dislikes: {
    type: Number,
    required: false,
    default: 0,
  },
});
</script>
