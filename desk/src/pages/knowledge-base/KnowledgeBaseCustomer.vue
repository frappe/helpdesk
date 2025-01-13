<template>
  <div class="p-5 px-10 w-full overflow-scroll items-center">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg font-medium text-gray-900">Knowledge base</div>
      </template>
    </LayoutHeader>
    <div class="max-w-4xl pt-4 sm:px-5 w-full flex flex-col gap-2">
      <FormControl
        ref="searchInputRef"
        type="text"
        class="w-full"
        placeholder="Ask a question..."
        size="lg"
        v-model="search"
      >
        <template #prefix>
          <Icon icon="lucide:search" class="h-4 w-4 text-gray-500" />
        </template>
      </FormControl>

      <!-- Searched Articles -->
      <div></div>

      <!-- Categories Folder -->
      <section>
        <!-- Heading -->
        <span
          class="text-base text-gray-600 font-medium leading-6 pl-1 my-0 mb-1"
        >
          Categories
        </span>
        <CategoryFolderContainer />
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { FormControl, usePageMeta, FeatherIcon } from "frappe-ui";
import { Icon } from "@iconify/vue";
import { LayoutHeader } from "@/components";
import CategoryFolderContainer from "@/components/knowledge-base/CategoryFolderContainer.vue";

const search = ref("");

usePageMeta(() => {
  return {
    title: "Knowledge base",
  };
});
</script>

<style scoped></style>
