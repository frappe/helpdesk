<template>
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
        {{ dayjs.tz(creation).fromNow() }}
      </div>
      <div class="text-base text-gray-300">|</div>
      <div class="text-gray-600">Modified</div>
      <div class="text-gray-800">
        {{ dayjs.tz(modified).fromNow() }}
      </div>
    </div>
  </div>
  <div class="border-b pb-3">
    <FormControl
      :value="title"
      type="text"
      @change="emit('update:title', $event.target.value)"
    />
  </div>
</template>

<script setup lang="ts">
import { Avatar, FormControl } from "frappe-ui";
import { dayjs } from "@/dayjs";

interface P {
  categoryName: string;
  subCategoryName: string;
  title: string;
  authorFullname: string;
  authorImage: string;
  creation: string;
  modified: string;
  likes?: number;
  dislikes?: number;
}

interface E {
  (event: "update:title", title: string): void;
}

defineProps<P>();
const emit = defineEmits<E>();
</script>
