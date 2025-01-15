<template>
  <div class="p-5 pb-10 md:pb-0 px-10 w-full overflow-scroll items-center">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg font-medium text-gray-900">Knowledge base</div>
      </template>
    </LayoutHeader>
    <div
      class="max-w-4xl 2xl:max-w-5xl pt-4 sm:px-5 w-full flex flex-col gap-4"
    >
      <FormControl
        ref="searchInputRef"
        type="text"
        class="w-full"
        placeholder="Ask a question..."
        size="lg"
        v-model="query"
      >
        <template #prefix>
          <Icon icon="lucide:search" class="h-4 w-4 text-gray-500" />
        </template>
      </FormControl>

      <!-- Searched Articles -->
      <div class="flex flex-col gap-3">
        <SearchArticles :query="query" :hideViewAll="true" />
      </div>

      <!-- Categories Folder -->
      <section class="flex flex-col gap-3">
        <!-- Heading -->
        <p class="text-lg text-gray-900">Categories</p>
        <CategoryFolderContainer />
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { FormControl, usePageMeta } from "frappe-ui";
import { Icon } from "@iconify/vue";
import { LayoutHeader } from "@/components";
import CategoryFolderContainer from "@/components/knowledge-base/CategoryFolderContainer.vue";
import SearchArticles from "../../components/SearchArticles.vue";
const query = ref("");

usePageMeta(() => {
  return {
    title: "Knowledge base",
  };
});
</script>

<style scoped></style>
