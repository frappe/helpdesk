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
      <Popover
        :popover-class="['max-w-[310px] md:max-w-[842px] !top-1 ']"
        class="flex w-full"
      >
        <template #target="{ open, close }">
          <FormControl
            ref="searchInputRef"
            type="text"
            class="w-full focus:outline-none outline-none border-inherit shadow-none"
            placeholder="Ask a question..."
            size="md"
            autofocus
            autocomplete="off"
            v-model="query"
            @update:model-value="
              (e:string) => {
                if (e.length >= 3) {
                  open();
                } else {
                  close();
                }
              }
            "
          >
            <template #prefix>
              <Icon icon="lucide:search" class="h-4 w-4 text-gray-500" />
            </template>
          </FormControl>
        </template>
        <template #body-main>
          <!-- Searched Articles -->
          <div
            class="max-h-[320px] md:max-h-[420px] overflow-scroll flex flex-col"
          >
            <SearchArticles
              :query="query"
              :hideViewAll="true"
              class="p-3 py-2 border-0 pt-2"
            />
          </div>
        </template>
      </Popover>

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
import { FormControl, usePageMeta, Popover } from "frappe-ui";
import { Icon } from "@iconify/vue";
import { LayoutHeader } from "@/components";
import CategoryFolderContainer from "@/components/knowledge-base/CategoryFolderContainer.vue";
import SearchArticles from "../../components/SearchArticles.vue";
import { capture } from "@/telemetry";

const query = ref("");
const searchInputRef = ref(null);

onMounted(() => {
  capture("kb_customer_page_viewed");
});
usePageMeta(() => {
  return {
    title: "Knowledge Base",
  };
});
</script>
