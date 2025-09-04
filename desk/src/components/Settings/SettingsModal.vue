<template>
  <Dialog
    v-model="show"
    :options="{ size: '5xl' }"
    :disableOutsideClickToClose="disableSettingModalOutsideClick"
  >
    <template #body>
      <div class="flex" :style="{ height: 'calc(100vh - 8rem)' }">
        <div class="flex w-52 shrink-0 flex-col bg-gray-50 p-2">
          <h1 class="px-2 pt-2 text-lg font-semibold">Settings</h1>
          <div class="mt-3 space-y-1">
            <button
              v-for="tab in tabs"
              :key="tab.label"
              class="flex h-7 w-full items-center gap-2 rounded px-2 py-1"
              :class="[
                activeTab?.label == tab.label
                  ? 'bg-white shadow-sm'
                  : 'hover:bg-gray-100',
              ]"
              @click="() => onTabChange(tab)"
            >
              <component :is="tab.icon" class="h-4 w-4 text-gray-700" />
              <span class="text-base text-gray-800">
                {{ tab.label }}
              </span>
            </button>
          </div>
        </div>
        <div class="flex flex-1 flex-col bg-surface-modal">
          <div class="flex justify-end p-2">
            <Button
              class="bg-white hover:bg-gray-4"
              @click="show = false"
              icon="x"
              size="md"
            />
          </div>
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
  type Tab,
  tabs,
} from "./settingsModal";

const props = withDefaults(
  defineProps<{
    defaultTab?: number;
  }>(),
  {
    defaultTab: 0,
  }
);

const show: ModelRef<boolean> = defineModel();

const showConfirmDialog = ref(false);

function onTabChange(tab: Tab) {
  if (!disableSettingModalOutsideClick.value) {
    activeTab.value = tab;
    return;
  }
  nextActiveTab.value = tab;
  showConfirmDialog.value = true;
}

watch(
  () => props.defaultTab,
  (val) => {
    activeTab.value = tabs[val];
  }
);
</script>
