<template>
  <Dialog v-model="show" :options="{ size: '4xl' }">
    <template #body>
      <div class="flex" :style="{ height: 'calc(100vh - 8rem)' }">
        <div class="flex w-52 shrink-0 flex-col bg-gray-50 p-2">
          <h1 class="px-2 pt-2 text-lg font-semibold">Settings</h1>
          <div class="mt-3">
            <button
              v-for="tab in tabs"
              :key="tab.label"
              class="flex h-7 w-full items-center gap-2 rounded px-2 py-1"
              :class="[
                activeTab?.label == tab.label
                  ? 'bg-white shadow-sm'
                  : 'hover:bg-gray-100',
              ]"
              @click="activeTab = tab"
            >
              <component :is="tab.icon" class="h-4 w-4 text-gray-700" />
              <span class="text-base text-gray-800">
                {{ tab.label }}
              </span>
            </button>
          </div>
        </div>
        <div class="flex flex-1 flex-col overflow-scroll p-4">
          <component :is="activeTab.component" v-if="activeTab" />
        </div>
      </div>
    </template>
  </Dialog>
</template>
<script setup lang="ts">
import { ModelRef, ref } from "vue";
import { Dialog } from "frappe-ui";
import LucideMail from "~icons/lucide/mail";
import ImageUp from "~icons/lucide/image-up";
import EmailConfig from "./EmailConfig.vue";
import Branding from "./Branding.vue";
let tabs = [
  {
    label: "Email Accounts",
    icon: LucideMail,
    component: EmailConfig,
  },
  {
    label: "Branding",
    icon: ImageUp,
    component: Branding,
  },
];
const show: ModelRef<boolean> = defineModel();
const activeTab = ref(tabs[0]);
</script>
