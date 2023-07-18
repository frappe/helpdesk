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
  </div>
  <div class="border-b pb-3">
    <FormControl
      type="text"
      placeholder="Title"
      @change="emit('update:title', $event.target.value)"
    />
  </div>
</template>

<script setup lang="ts">
import { Avatar, FormControl } from "frappe-ui";
import IconChevronRight from "~icons/lucide/chevron-right";

interface P {
  categoryName: string;
  subCategoryName: string;
  title: string;
  authorFullname: string;
  authorImage: string;
}

interface E {
  (event: "update:title", title: string): void;
}

defineProps<P>();
const emit = defineEmits<E>();
</script>
