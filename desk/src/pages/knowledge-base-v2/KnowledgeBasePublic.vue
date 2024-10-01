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
        v-if="currentCategory !== 'Explore All Articles'"
        :category-id="currentCategory"
      />
      <div v-else>All</div>
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
const defaultCategory = router.currentRoute.value.query.category as string;

const currentCategory: Ref<string> = ref(
  defaultCategory || "Explore All Articles"
);

const breadcrumbs = computed(() => {
  let items = [
    { label: "Knowledge Base", route: { name: "KnowledgeBasePublicNew" } },
  ];
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
