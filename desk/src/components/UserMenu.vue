<template>
  <Dropdown :options="options">
    <template #default="{ open }">
      <button
        class="flex h-12 items-center rounded-md p-1 duration-300 ease-in-out w-full"
        :class="open ? 'bg-white text-ink-gray-9 shadow-sm' : 'text-ink-white hover:bg-white/10'"
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
            class="text-base font-medium leading-none truncate"
            :class="open ? 'text-ink-gray-9' : 'text-ink-white'"
          >
            {{ config.brandName || "Helpdesk" }}
          </div>
          <div
            class="mt-1 text-sm leading-none"
            :class="open ? 'text-ink-gray-7' : 'text-ink-gray-2'"
          >
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
            class="h-4 w-4"
            :class="open ? 'text-ink-gray-7' : 'text-ink-gray-2'"
            aria-hidden="true"
          />
        </div>
      </button>
    </template>
  </Dropdown>
</template>

<script setup lang="ts">
import { Dropdown, Avatar } from "frappe-ui";
import { useAuthStore } from "@/stores/auth";
import { useSidebarStore } from "@/stores/sidebar";
import { useConfigStore } from "@/stores/config";
import BrandLogo from "@/components/BrandLogo.vue";

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
