<template>
  <div class="p-5 px-10 w-full overflow-scroll items-center">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg font-medium text-gray-900">Knowledge base</div>
      </template>
    </LayoutHeader>
    <div class="max-w-4xl pt-4 sm:px-5 w-full flex flex-col gap-2">
      {{ categoryId }}
    </div>
    <div v-if="articles.data" class="text-wrap flex-1">
      {{ articles.data }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { createListResource } from "frappe-ui";
import LayoutHeader from "@/components/LayoutHeader.vue";
const props = defineProps({
  categoryId: {
    required: true,
    type: String,
  },
});

const articles = createListResource({
  doctype: "HD Article",
  fields: ["author", "title", "modified"],
  filters: {
    category: props.categoryId,
    status: "Published",
  },
  auto: true,
});
</script>

<style scoped></style>
