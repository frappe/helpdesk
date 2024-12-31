<template>
  <div
    class="h-full space-y-2 border-r px-3.5 py-2.5"
    :style="{
      'min-width': '242px',
      'max-width': '242px',
    }"
  >
    <div class="flex flex-col gap-1">
      <div
        class="text-sm font-medium text-gray-600 mb-1 flex justify-between items-center"
      >
        <p>Categories</p>
        <p>as</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import SidebarLink from "../SidebarLink.vue";
import { createListResource, Tree } from "frappe-ui";
import { getIcon } from "@/pages/knowledge-base/util";
const emit = defineEmits(["category-change"]);

const activeCategory = defineModel();

const categories = createListResource({
  doctype: "HD Article Category",
  auto: true,
  fields: ["name", "category_name", "icon", "parent_category"],
  filters: {
    parent_category: "",
  },
  transform: (data) => {
    const firstCategory = {
      name: "Explore all articles",
      category_name: "Explore all articles",
      icon: "search",
    };
    return [firstCategory, ...data];
  },
});

function handleClick(name: string) {
  if (activeCategory.value === name) return;
  activeCategory.value = name;
}
</script>

<style scoped></style>
