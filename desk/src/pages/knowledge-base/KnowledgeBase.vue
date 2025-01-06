<template>
  <div class="flex flex-col">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg font-medium text-gray-900">Knowledge base</div>
      </template>
      <template #right-header>
        <Button
          label="New article"
          variant="solid"
          @click="() => $router.push('/articles/new')"
        >
          <template #prefix>
            <LucidePlus class="h-4 w-4" />
          </template>
        </Button>
      </template>
    </LayoutHeader>
    <!-- ListView Grouped By Status -->
    <!-- <KnowledgeBaseListView /> -->
    <ListViewBuilder
      :options="options"
      @row-click="(row) => $router.push(`kb/articles/${row}`)"
    />
  </div>
</template>

<script setup lang="ts">
import { usePageMeta, createListResource } from "frappe-ui";
import LayoutHeader from "@/components/LayoutHeader.vue";
import ArticleCard from "@/components/knowledge-base/ArticleCard.vue";
import { Article } from "@/types";
import KnowledgeBaseListView from "@/components/knowledge-base/KnowledgeBaseListView.vue";
import ListViewBuilder from "@/components/ListViewBuilder.vue";

const options = {
  doctype: "HD Article",
  view: {
    view_type: "group_by",
    group_by_field: "category",
  },
  statusMap: {
    Published: {
      label: "Published",
      theme: "green",
    },
    Draft: {
      label: "Draft",
      theme: "gray",
    },
  },
};

usePageMeta(() => {
  return {
    title: "Knowledge base",
  };
});
</script>
