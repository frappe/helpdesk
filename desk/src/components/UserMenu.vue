<template>
  <Dropdown :options="options">
    <template #default="{ open }">
      <button
        class="flex h-12 items-center rounded-md py-2 duration-300 ease-in-out"
        :class="
          !sidebarStore.isExpanded
            ? 'w-auto px-0'
            : open
            ? 'w-full px-2 bg-surface-white shadow-sm'
            : 'w-full px-2 hover:bg-surface-gray-3'
        "
      >
        <BrandLogo />
        <div
          class="flex flex-1 flex-col text-left duration-300 ease-in-out overflow-hidden"
          :class="
            !sidebarStore.isExpanded
              ? 'ml-0 w-0 overflow-hidden opacity-0'
              : 'ml-2 w-auto opacity-100'
          "
        >
          <div
            class="text-base font-medium leading-none text-gray-900 truncate"
          >
            {{ config.brandName || "Helpdesk" }}
          </div>
          <div class="mt-1 text-sm leading-none text-gray-700">
            {{ authStore.userName }}
          </div>
        </div>
        <div
          class="duration-300 ease-in-out"
          :class="
            !sidebarStore.isExpanded
              ? 'ml-0 w-0 overflow-hidden opacity-0'
              : 'ml-2 w-auto opacity-100'
          "
        >
          <FeatherIcon
            name="chevron-down"
            class="h-4 w-4 text-gray-600"
            aria-hidden="true"
          />
        </div>
      </button>
    </template>
  </Dropdown>
</template>

<script setup lang="ts">
import BrandLogo from "@/components/BrandLogo.vue";
import { useAuthStore } from "@/stores/auth";
import { useConfigStore } from "@/stores/config";
import { useSidebarStore } from "@/stores/sidebar";
import { Dropdown } from "frappe-ui";

const config = useConfigStore();

defineProps({
  options: {
    type: Array,
    required: true,
  },
});

const authStore = useAuthStore();
const sidebarStore = useSidebarStore();
</script>
