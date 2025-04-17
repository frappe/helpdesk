<template>
  <div class="p-5 pb-10 px-10 w-full overflow-scroll items-center">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg font-medium text-gray-900">Knowledge Base</div>
      </template>
    </LayoutHeader>
    <div
      class="max-w-4xl 2xl:max-w-5xl pt-4 sm:px-5 w-full flex flex-col gap-4"
    >
      <SearchPopover
        :popoverClass="['max-w-[310px] md:max-w-[842px] !top-1']"
        v-model="query"
        placeholder="Ask a question..."
        size="md"
        :autofocus="true"
      />

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
import { ref, onMounted } from "vue";
import { usePageMeta } from "frappe-ui";

import { LayoutHeader } from "@/components";
import CategoryFolderContainer from "@/components/knowledge-base/CategoryFolderContainer.vue";
import SearchPopover from "@/components/SearchPopover.vue";
import { capture } from "@/telemetry";

const query = ref("");

onMounted(() => {
  capture("kb_customer_page_viewed");
});
usePageMeta(() => {
  return {
    title: "Knowledge Base",
  };
});
</script>
