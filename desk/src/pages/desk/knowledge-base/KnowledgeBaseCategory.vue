<template>
  <div class="grow px-5 py-3.5">
    <div class="mb-6 space-y-1">
      <div class="flex items-center justify-between">
        <div class="text-xl font-medium text-gray-900">
          {{ category.doc?.category_name }}
        </div>
        <div class="space-x-2">
          <Button label="Edit" theme="gray" variant="outline"
            ><template #prefix><IconEdit class="h-4 w-4" /></template
          ></Button>
          <Button label="Add new" theme="gray" variant="solid"
            ><template #prefix><IconPlus class="h-4 w-4" /></template
          ></Button>
        </div>
      </div>
      <div
        class="text-base text-gray-700"
        :style="{
          width: '770px',
        }"
      >
        {{ category.doc?.description }}
      </div>
    </div>
    <div class="gap-5.5 grid grid-cols-3">
      <KnowledgeBaseCategoryCard
        v-for="c in subCategories.data"
        :key="c.name"
        class="place-self-center"
        :title="c.category_name"
        :description="c.description"
        :article-count="c.count_article"
      />
    </div>
  </div>
</template>
<script setup lang="ts">
import { createDocumentResource, Button } from "frappe-ui";
import { createListManager } from "@/composables/listManager";
import KnowledgeBaseCategoryCard from "./KnowledgeBaseCategoryCard.vue";
import IconEdit from "~icons/lucide/edit-3";
import IconPlus from "~icons/lucide/plus";

const category = createDocumentResource({
  doctype: "HD Article Category",
  name: "dd01268bcc",
  auto: true,
});

const subCategories = createListManager({
  doctype: "HD Article Category",
  filters: {
    parent_category: "dd01268bcc",
  },
  auto: true,
});
</script>
