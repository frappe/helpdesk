<template>
  <span>
    <header class="bg-gray-100">
      <div class="container m-auto">
        <div class="py-12">
          <div class="flex items-center gap-2">
            <RouterLink :to="{ name: CUSTOMER_PORTAL_LANDING }">
              <img :src="Logo" class="h-5" />
            </RouterLink>
            <span class="text-gray-600">/</span>
            <span class="font-medium text-gray-900">Knowledge Base</span>
          </div>
          <div
            class="my-4 flex w-max cursor-pointer items-center gap-2 rounded bg-white px-3 py-2 text-gray-600 shadow"
            @click="showSearch = !showSearch"
          >
            <Icon icon="lucide:search" class="h-4 w-4 text-gray-800" />
            <span
              >Search for an answer or browse help topics to create a
              ticket</span
            >
            <span class="ml-3 flex items-center gap-1 text-gray-800">
              <Icon icon="lucide:command" class="h-4 w-4" />
              K
            </span>
          </div>
          <div class="flex flex-wrap gap-4">
            <RouterLink
              class="w-max cursor-pointer border-b-2 border-b-gray-400 pb-1 text-gray-900 hover:border-b-gray-600"
              :to="{ name: CUSTOMER_PORTAL_LANDING }"
            >
              Track tickets
            </RouterLink>
            <RouterLink
              v-for="article in topArticles.data"
              :key="article.name"
              class="w-max cursor-pointer border-b-2 border-b-gray-400 pb-1 text-gray-900 hover:border-b-gray-600"
              :to="{
                name: KB_PUBLIC_ARTICLE,
                params: { articleId: article.name },
              }"
            >
              {{ article.title }}
            </RouterLink>
          </div>
        </div>
      </div>
    </header>
    <RouterView :key="$route.fullPath" class="container m-auto" />
    <KnowledgeBasePublicSearch v-model="showSearch" />
  </span>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";
import { createListResource } from "frappe-ui";
import { Icon } from "@iconify/vue";
import { CUSTOMER_PORTAL_LANDING, KB_PUBLIC_ARTICLE } from "@/router";
import { useKeymapStore } from "@/stores/keymap";
import Logo from "@/assets/logos/helpdesk.svg";
import KnowledgeBasePublicSearch from "./KnowledgeBasePublicSearch.vue";

const keymapStore = useKeymapStore();
const showSearch = ref(false);
const topArticles = createListResource({
  doctype: "HD Article",
  pageLength: 5,
  orderBy: "views desc",
  auto: true,
  filters: {
    status: "Published",
  },
  fields: ["name", "title"],
});

const mapping = ["meta", "k"];
onMounted(() =>
  keymapStore.add(mapping, () => (showSearch.value = !showSearch.value))
);
onUnmounted(() => keymapStore.remove(mapping));
</script>
