<template>
  <div class="container my-8 grid grid-cols-3 gap-4">
    <div v-for="category in data.data" :key="category.name" class="space-y-4">
      <div class="flex items-center gap-2 text-gray-800">
        <component :is="getIcon(category.icon)" class="h-4 w-4" />
        <div class="text-lg font-medium">
          {{ category.category_name }}
        </div>
      </div>
      <div class="ml-6 space-y-2 text-base text-gray-700">
        <div
          v-for="subCategory in category.sub_categories"
          :key="subCategory.name"
          class="w-max cursor-pointer border-b border-b-transparent pb-1 hover:border-b-gray-700"
          @click="toCategory(subCategory.name)"
        >
          {{ subCategory.category_name }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";
import { createResource } from "frappe-ui";
import { KB_PUBLIC_CATEGORY } from "@/router";
import { getIcon } from "./util";

const router = useRouter();
const data = createResource({
  url: "helpdesk.helpdesk.doctype.hd_article_category.api.get_list_public",
  auto: true,
});

function toCategory(categoryId: string) {
  router.push({
    name: KB_PUBLIC_CATEGORY,
    params: {
      categoryId,
    },
  });
}
</script>
