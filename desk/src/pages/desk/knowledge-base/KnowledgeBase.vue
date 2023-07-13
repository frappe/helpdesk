<template>
  <div class="flex flex-col">
    <PageTitle title="Knowledge base" />
    <div class="flex grow border-t">
      <div
        class="h-full space-y-2 border-r px-3.5 py-2.5"
        :style="{
          'min-width': '242px',
          'max-width': '242px',
        }"
      >
        <div class="flex items-center justify-between">
          <div class="text-sm font-medium text-gray-600">Categories</div>
          <Button theme="gray" variant="ghost">
            <template #icon>
              <IconMoreHorizontal class="h-4 w-4" />
            </template>
          </Button>
        </div>
        <div class="flex flex-col gap-1">
          <SidebarLink
            v-for="category in categories.data"
            :key="category.label"
            :icon="IconBox"
            :label="category.category_name"
          />
        </div>
      </div>
      <!-- <KnowledgeBaseCategory /> -->
      <KnowledgeBaseSubcategory />
    </div>
  </div>
</template>

<script setup lang="ts">
import { createListResource, Button } from "frappe-ui";
import PageTitle from "@/components/PageTitle.vue";
import SidebarLink from "@/components/SidebarLink.vue";
import KnowledgeBaseCategory from "./KnowledgeBaseCategory.vue";
import KnowledgeBaseSubcategory from "./KnowledgeBaseSubcategory.vue";
import IconBox from "~icons/lucide/box";
import IconMoreHorizontal from "~icons/lucide/more-horizontal";

const categories = createListResource({
  doctype: "HD Article Category",
  auto: true,
  fields: ["name", "category_name"],
  filters: {
    parent_category: "",
  },
});
</script>
