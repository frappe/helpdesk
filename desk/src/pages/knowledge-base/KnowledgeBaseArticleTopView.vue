<template>
  <div class="mb-7 flex items-center justify-between">
    <div class="flex items-center gap-1">
      <div class="flex items-center gap-2">
        <Avatar :label="authorFullname" :image="authorImage" />
        <div class="text-base text-gray-800">
          {{ authorFullname }}
        </div>
      </div>
      <IconDot class="h-4 w-4 text-gray-600" />
      <div class="text-xs text-gray-500">
        {{ dayjs(creation).short() }}
      </div>
      <div v-if="!isCustomerPortal" class="flex items-center justify-center">
        <IconDot class="h-4 w-4 text-gray-600" />
        <Badge
          :theme="status === 'Published' ? 'green' : 'orange'"
          variant="subtle"
        >
          {{ status }}
        </Badge>
      </div>
    </div>
  </div>
  <div class="border-b pb-3">
    <div class="text-2xl font-semibold text-gray-900">
      {{ title }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { Avatar } from "frappe-ui";
import { dayjs } from "@/dayjs";
import IconDot from "~icons/lucide/dot";
import { useRoute } from "vue-router";

const route = useRoute();
const isCustomerPortal: boolean = route.meta.public ?? false;

const props = defineProps({
  categoryName: {
    type: String,
    required: true,
  },
  categoryId: {
    type: String,
    required: true,
  },
  subCategoryName: {
    type: String,
    required: true,
  },
  subCategoryId: {
    type: String,
    required: true,
  },
  title: {
    type: String,
    required: true,
  },
  status: {
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
});
</script>
