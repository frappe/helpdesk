<template>
  <div class="container my-8">
    <div class="mb-8 flex items-center gap-2">
      <RouterLink :to="{ name: KB_PUBLIC }">
        <Icon icon="lucide:home" class="h-4 w-4" />
      </RouterLink>
      <Icon icon="lucide:chevron-right" class="h-4 w-4 text-gray-600" />
      <div class="text-base font-medium text-gray-900">
        {{ category.doc?.category_name }}
      </div>
    </div>
    <ul class="space-y-2">
      <li
        v-for="article in articles.data"
        :key="article.name"
        class="w-max cursor-pointer border-b border-b-transparent pb-1 text-base text-gray-800 hover:border-b-gray-700"
        @click="toArticle(article.name)"
      >
        {{ article.title }}
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";
import { createDocumentResource, createListResource } from "frappe-ui";
import { Icon } from "@iconify/vue";
import { KB_PUBLIC, KB_PUBLIC_ARTICLE } from "@/router";

interface P {
  categoryId: string;
}

const props = defineProps<P>();
const router = useRouter();

const category = createDocumentResource({
  doctype: "HD Article Category",
  name: props.categoryId,
  auto: true,
});

const articles = createListResource({
  doctype: "HD Article",
  fields: ["name", "title"],
  filters: {
    category: props.categoryId,
    status: "Published",
  },
  auto: true,
});

function toArticle(articleId: string) {
  router.push({
    name: KB_PUBLIC_ARTICLE,
    params: {
      articleId,
    },
  });
}
</script>
