<template>
  <div
    class="h-full space-y-2 border-r px-3.5 py-2.5"
    :style="{
      'min-width': '242px',
      'max-width': '242px',
    }"
  >
    <div class="flex flex-col gap-1">
      <div class="text-sm font-medium text-gray-600">Categories</div>
      <div v-if="!categories.isLoading" class="flex flex-col gap-1">
        <!-- all categories here -->
        <SidebarLink
          v-for="category in categories.data"
          :key="category.label"
          :icon="getIcon(category.icon, true)"
          :is-active="activeCategory === category.name"
          :is-expanded="true"
          :label="category.category_name"
          :bg-color="'bg-gray-100'"
          @click="handleClick(category.name)"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import SidebarLink from "../SidebarLink.vue";
import { createListResource } from "frappe-ui";
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
      name: "Explore All Articles",
      category_name: "Explore All Articles",
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
