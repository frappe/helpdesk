<template>
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

interface P {
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
