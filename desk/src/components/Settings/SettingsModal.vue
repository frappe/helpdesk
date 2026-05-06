<template>
  <Dialog
    v-model="show"
    :options="{ size: '5xl' }"
    :disableOutsideClickToClose="disableSettingModalOutsideClick"
  >
    <template #body>
      <div
        class="flex z-50 overflow-hidden"
        :style="{ height: 'calc(100vh - 8rem)' }"
      >
        <div
          class="flex-col rounded-l-lg w-56 shrink-0 bg-gray-50 m-1 bg-surface-menu-bar overflow-y-auto hide-scrollbar"
        >
          <h1
            class="h-7.5 px-2 py-[7px] my-[3px] flex cursor-pointer gap-1.5 text-xs font-medium text-ink-gray-5 transition-all duration-300 ease-in-out sticky top-0 z-10 bg-surface-menu-bar"
          >
            {{ __("Account") }}
          </h1>
          <div v-for="tab in tabs" class="last:mb-2">
            <div v-if="!tab.noborder" class="mx-2 my-2.5"></div>

            <div
              v-if="!tab.hideLabel"
              class="h-7.5 px-2 py-[7px] my-[3px] flex cursor-pointer gap-1.5 text-xs font-medium text-ink-gray-5 transition-all duration-300 ease-in-out sticky top-0 z-10 bg-surface-menu-bar"
            >
              <Tooltip :text="__(tab.label)" placement="right">
                <span class="truncate">{{ __(tab.label) }}</span>
              </Tooltip>
            </div>

            <nav class="space-y-[3px] px-1">
              <button
                v-for="item in tab.items"
                :key="item.label"
                class="flex h-7 w-full items-center gap-2 rounded px-2 py-[7px]"
                :class="[
                  activeTab?.label == item.label
                    ? 'bg-white shadow-sm'
                    : 'hover:bg-gray-100',
                ]"
                @click="() => onTabChange(item)"
              >
                <component
                  :is="item.icon"
                  class="h-4 w-4 text-gray-700 shrink-0"
                />
                <Tooltip :text="__(item.label)" placement="right">
                  <span class="text-p-sm text-gray-800 truncate">
                    {{ __(item.label) }}
                  </span>
                </Tooltip>
              </button>
            </nav>
          </div>
        </div>
        <div
          class="flex flex-1 flex-col bg-surface-modal max-w-[816px] overflow-hidden"
        >
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
