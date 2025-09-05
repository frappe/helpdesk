<template>
  <Dialog
    v-model="show"
    :options="{ size: '5xl' }"
    :disableOutsideClickToClose="disableSettingModalOutsideClick"
  >
    <template #body>
      <div class="flex" :style="{ height: 'calc(100vh - 8rem)' }">
        <div class="flex w-52 shrink-0 flex-col bg-gray-50 p-2">
          <h1 class="px-2 pt-2 text-lg font-semibold mb-3">Settings</h1>
          <div v-for="tab in tabs">
            <div
              v-if="!tab.hideLabel"
              class="mb-2 mt-3 flex gap-1.5 px-1 text-base font-medium text-ink-gray-5"
            >
              <span>{{ __(tab.label) }}</span>
            </div>
            <nav class="space-y-1">
              <button
                v-for="item in tab.items"
                :key="item.label"
                class="flex h-7 w-full items-center gap-2 rounded px-2 py-1"
                :class="[
                  activeTab?.label == item.label
                    ? 'bg-white shadow-sm'
                    : 'hover:bg-gray-100',
                ]"
                @click="() => onTabChange(item)"
              >
                <component :is="item.icon" class="h-4 w-4 text-gray-700" />
                <span class="text-base text-gray-800">
                  {{ item.label }}
                </span>
              </button>
            </nav>
          </div>
        </div>
        <div class="flex flex-1 flex-col bg-surface-modal">
          <component
            :is="activeTab.component"
            v-if="activeTab"
            class="h-full flex flex-col w-full"
          />
        </div>
      </div>
    </template>
  </Dialog>
  <ConfirmDialog
    v-model="showConfirmDialog"
    :title="__('Unsaved changes')"
    :message="
      __('Are you sure you want to change tabs? Unsaved changes will be lost.')
    "
    :onConfirm="
      () => {
        if (nextActiveTab !== null) {
          activeTab = nextActiveTab;
        }
        nextActiveTab = null;
        showConfirmDialog = false;
        disableSettingModalOutsideClick = false;
      }
    "
    :onCancel="
      () => {
        nextActiveTab = null;
      }
    "
  />
</template>
<script setup lang="ts">
import { Dialog } from "frappe-ui";
import { ModelRef, ref, watch } from "vue";
import ConfirmDialog from "@/components/ConfirmDialog.vue";
import {
  activeTab,
  disableSettingModalOutsideClick,
  nextActiveTab,
  tabs,
} from "./settingsModal";

const show: ModelRef<boolean> = defineModel();

const showConfirmDialog = ref(false);

function onTabChange(tab) {
  if (!disableSettingModalOutsideClick.value) {
    activeTab.value = tab;
    return;
  }
  nextActiveTab.value = tab;
  showConfirmDialog.value = true;
}
</script>
