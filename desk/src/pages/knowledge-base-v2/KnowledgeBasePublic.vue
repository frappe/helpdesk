<template>
  <div class="flex flex-col">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="breadcrumbs" />
      </template>
    </LayoutHeader>
    <div class="flex grow overflow-hidden">
      <KnowledgeBaseSidebar v-model="currentCategory" />
      <KnowledgeBaseCategory
        v-if="currentCategory !== 'Explore all articles'"
        :category-id="currentCategory"
      />
      <KnowledgeBaseCategory v-else show-all-articles />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, Ref } from "vue";
import { LayoutHeader } from "@/components";
import KnowledgeBaseSidebar from "@/components/knowledge-base-v2/KnowledgeBaseSidebar.vue";
import KnowledgeBaseCategory from "@/components/knowledge-base-v2/KnowledgeBaseCategory.vue";
import { useRouter } from "vue-router";
import { Breadcrumbs } from "frappe-ui";

const router = useRouter();
const defaultCategory = computed(
  () => router.currentRoute.value.query.category as string
);

const currentCategory = ref(defaultCategory.value || "Explore all articles");

const breadcrumbs = computed(() => {
  const { category, subCategory } = router.currentRoute.value.query as {
    category: string;
    subCategory: string;
  };
  let items = [
    {
      label: "Knowledge Base",
      route: {
        name: "KnowledgeBasePublicNew",
        query: { category },
      },
    },
  ];
  // return items;
  // TODO: Add category and subcategory name to breadcrumbs

  if (category) {
    items.push({
      label: category,
      route: {
        name: "KnowledgeBasePublicNew",
        query: { category },
      },
    });
  }
  if (subCategory) {
    items.push({
      label: subCategory,
      route: { name: "KnowledgeBasePublicNew", query: { subCategory } },
    });
  }
  return items;
});

watch(
  () => currentCategory.value,
  () => {
    router.push({
      query: {
        category: currentCategory.value,
      },
    });
  }
);
</script>

<style scoped></style>
