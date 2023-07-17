<template>
  <div
    class="h-full space-y-2 border-r px-3.5 py-2.5"
    :style="{
      'min-width': '242px',
      'max-width': '242px',
    }"
  >
    <div class="flex items-center justify-between">
      <div class="text-sm font-medium text-gray-600">Categories</div>
      <Button
        theme="gray"
        variant="ghost"
        @click="showNewDialog = !showNewDialog"
      >
        <template #icon>
          <Icon icon="lucide:plus" class="h-4 w-4" />
        </template>
      </Button>
    </div>
    <div class="flex flex-col gap-1">
      <SidebarLink
        v-for="category in categories.data"
        :key="category.label"
        :icon="getIcon(category.icon)"
        :is-active="activeCategory === category.name"
        :label="category.category_name"
        @click="activeCategory = category.name"
      />
    </div>
    <KnowledgeBaseCategoryNew
      v-model="showNewDialog"
      @success="onNewCategory"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { createListResource, Button } from "frappe-ui";
import { storeToRefs } from "pinia";
import { Icon } from "@iconify/vue";
import SidebarLink from "@/components/SidebarLink.vue";
import KnowledgeBaseCategoryNew from "./KnowledgeBaseCategoryNew.vue";
import { useKnowledgeBaseStore } from "./data";
import { getIcon } from "./util";

const { activeCategory } = storeToRefs(useKnowledgeBaseStore());
const categories = createListResource({
  doctype: "HD Article Category",
  auto: true,
  fields: ["name", "category_name", "icon"],
  filters: {
    parent_category: "",
  },
});
const showNewDialog = ref(false);

function onNewCategory(categoryId: string) {
  categories.reload().then(() => {
    showNewDialog.value = false;
    activeCategory.value = categoryId;
  });
}
</script>
