<template>
  <router-link
    class="flex flex-col gap-2 rounded-lg border p-3 w-[162px] sm:w-[172px] border-gray-200 cursor-pointer hover:shadow-xl"
    :to="{
      name: 'Articles',
      params: {
        categoryId: category.name,
      },
    }"
  >
    <Tooltip :text="category.category_name">
      <div>
        <FeatherIcon
          name="folder"
          class="fill-ink-blue-link h-8 w-8 text-blue-400"
        />
      </div>
      <div class="gap-1 flex flex-col">
        <p class="text-base font-medium text-gray-800 truncate">
          {{ category.category_name }}
        </p>
        <span class="truncate text-sm text-gray-600">
          {{ dayjs.tz(category.modified).fromNow() }}
        </span>
      </div>
    </Tooltip>
  </router-link>
</template>

<script setup lang="ts">
import { FeatherIcon, Tooltip } from "frappe-ui";
import { dayjs } from "@/dayjs";
const props = defineProps({
  category: {
    required: true,
    type: Object,
  },
});
</script>

<style scoped></style>
