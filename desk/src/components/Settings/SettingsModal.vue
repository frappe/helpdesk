<template>
  <Dialog
    v-model="show"
    :options="{ size: '5xl' }"
    :disableOutsideClickToClose="disableSettingModalOutsideClick"
  >
    <template #body>
      <div class="flex z-50" :style="{ height: 'calc(100vh - 8rem)' }">
        <div
          class="flex w-52 shrink-0 flex-col bg-gray-50 p-2 overflow-y-auto hide-scrollbar"
        >
<<<<<<< HEAD
          <h1 class="px-2 pt-2 text-lg font-semibold mb-2">
            {{ __("Settings") }}
=======
          <h1
            class="h-7.5 px-2 py-[7px] my-[3px] flex cursor-pointer gap-1.5 text-base text-ink-gray-5 transition-all duration-300 ease-in-out truncate"
          >
            {{ __("My Settings") }}
>>>>>>> 2d583532 (fix: truncate text for translations in settings menu)
          </h1>
          <div v-for="tab in tabs">
            <div
              v-if="!tab.hideLabel"
              class="mb-2 mt-3 flex gap-1.5 px-1 text-base font-medium text-ink-gray-5"
            >
              <Tooltip :text="__(tab.label)" placement="right">
                <span class="truncate">{{ __(tab.label) }}</span>
              </Tooltip>
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
<<<<<<< HEAD
                <component :is="item.icon" class="h-4 w-4 text-gray-700" />
<<<<<<< HEAD
                <span class="text-base text-gray-800">
                  {{ item.label }}
                </span>
=======
                <Tooltip :text="item.label">
=======
                <component
                  :is="item.icon"
                  class="h-4 w-4 text-gray-700 shrink-0"
                />
<<<<<<< HEAD
                <Tooltip :text="item.label" placement="right">
>>>>>>> c3079c90 (fix: truncation bugs for mobile and sidebar)
=======
                <Tooltip :text="__(item.label)" placement="right">
>>>>>>> 4b458035 (fix: add translation for tooltip labels)
                  <span class="text-p-sm text-gray-800 truncate">
                    {{ __(item.label) }}
                  </span>
                </Tooltip>
>>>>>>> 2d583532 (fix: truncate text for translations in settings menu)
              </button>
            </nav>
          </div>
        </div>
        <div class="flex flex-1 flex-col bg-surface-modal max-w-[816px]">
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
import { Dialog, Tooltip } from "frappe-ui";
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
