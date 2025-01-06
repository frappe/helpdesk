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
import { h } from "vue";
import { usePageMeta, FeatherIcon, Button } from "frappe-ui";

import LayoutHeader from "@/components/LayoutHeader.vue";
import ListViewBuilder from "@/components/ListViewBuilder.vue";

const groupByActions = [
  {
    label: "Add New Article",
    icon: "plus",
    onClick: (groupedRow) => {
      console.log("Add Article", groupedRow);
    },
  },
  {
    label: "Edit Title",
    icon: "edit",
    onClick: (groupedRow) => {
      console.log("Edit Title", groupedRow);
    },
  },
  {
    label: "Delete",
    icon: "trash-2",
    onClick: (groupedRow) => {
      console.log("Delete", groupedRow);
    },
  },
];

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
      theme: "orange",
    },
  },
  columnConfig: {
    title: {
      prefix: () => {
        return h(FeatherIcon, {
          name: "file",
          class: "w-4 h-4",
        });
      },
    },
  },
  groupByActions,
};

usePageMeta(() => {
  return {
    title: "Knowledge base",
  };
});
</script>
