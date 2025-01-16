<template>
  <div class="p-5 pb-10 px-10 w-full overflow-scroll items-center">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="breadcrumbs" />
      </template>
    </LayoutHeader>
    <div
      class="pt-4 sm:px-5 w-full flex flex-col gap-2 max-w-4xl 2xl:max-w-5xl"
    >
      <div v-if="articles.data" class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <ArticleCard2
          v-for="article in articles.data"
          :article="article"
          :key="article.name"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed } from "vue";
import { articles, categoryName } from "@/stores/knowledgeBase";
import { Breadcrumbs } from "frappe-ui";
import LayoutHeader from "@/components/LayoutHeader.vue";
import ArticleCard2 from "@/components/knowledge-base/ArticleCard2.vue";
const props = defineProps({
  categoryId: {
    required: true,
    type: String,
  },
});

onMounted(() => {
  articles.fetch({ category: props.categoryId });
  categoryName.fetch({
    category: props.categoryId,
  });
});

const categoryTitle = computed(() => {
  if (!categoryName.data) return;
  return categoryName.data;
});

const breadcrumbs = computed(() => {
  return [
    {
      label: "Knowledge Base",
      route: {
        name: "CustomerKnowledgeBase",
      },
    },
    {
      label: categoryTitle.value,
    },
  ];
});
</script>

<style scoped></style>
