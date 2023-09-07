<template>
  <span>
    <header class="bg-gray-100">
      <div class="container m-auto">
        <div class="flex justify-between py-2">
          <div class="flex items-center gap-2">
            <RouterLink :to="{ name: CUSTOMER_PORTAL_LANDING }">
              <img :src="Logo" class="h-5" />
            </RouterLink>
            <span class="text-gray-600">/</span>
            <span class="font-medium text-gray-900">Knowledge Base</span>
          </div>
          <Button
            label="Search"
            theme="gray"
            variant="outline"
            @click="showSearch = !showSearch"
          >
            <template #prefix>
              <Icon icon="lucide:search" />
            </template>
            <template #suffix>
              <span class="flex items-center gap-1">
                <Icon icon="lucide:command" class="h-3 w-3" />
                K
              </span>
            </template>
          </Button>
        </div>
      </div>
    </header>
    <RouterView :key="$route.fullPath" class="m-auto" />
    <KnowledgeBasePublicSearch v-model="showSearch" />
  </span>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";
import { Button } from "frappe-ui";
import { Icon } from "@iconify/vue";
import { CUSTOMER_PORTAL_LANDING } from "@/router";
import { useKeymapStore } from "@/stores/keymap";
import Logo from "@/assets/logos/helpdesk.svg";
import KnowledgeBasePublicSearch from "./KnowledgeBasePublicSearch.vue";

const keymapStore = useKeymapStore();
const showSearch = ref(false);
const mapping = ["meta", "k"];
onMounted(() =>
  keymapStore.add(mapping, () => (showSearch.value = !showSearch.value))
);
onUnmounted(() => keymapStore.remove(mapping));
</script>
