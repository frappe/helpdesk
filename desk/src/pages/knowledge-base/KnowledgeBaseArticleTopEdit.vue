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
        {{ dayjs(creation).fromNow() }}
      </div>
      <div class="text-base text-gray-300">|</div>
      <div class="text-gray-600">Modified</div>
      <div class="text-gray-800">
        {{ dayjs(modified).fromNow() }}
      </div>
      <div class="text-base text-gray-300">|</div>
      <Icon icon="lucide:thumbs-up" class="h-4 w-4" />
      <div class="text-gray-600">Likes</div>
      <div class="text-gray-800">
        {{ likes }}
      </div>
      <div class="text-base text-gray-300">|</div>
      <Icon icon="lucide:thumbs-down" class="h-4 w-4" />
      <div class="text-gray-600">Dislikes</div>
      <div class="text-gray-800">
        {{ dislikes }}
      </div>
    </div>
  </div>
  <div class="border-b pb-3">
    <FormControl
      :placeholder="title"
      type="text"
      @change="emit('update:title', $event.target.value)"
    />
  </div>
</template>

<script setup lang="ts">
import { Avatar, FormControl } from "frappe-ui";
import { dayjs } from "@/dayjs";
import { Icon } from "@iconify/vue";

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

withDefaults(defineProps<P>(), {
  likes: 0,
  dislikes: 0,
});
const emit = defineEmits<E>();
</script>
