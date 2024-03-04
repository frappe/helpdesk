<template>
  <Dropdown :options="options">
    <template #default="{ open }">
      <button
        class="flex h-12 items-center rounded-md py-2 duration-300 ease-in-out"
        :class="
          !sidebarStore.isExpanded
            ? 'px-0 w-auto'
            : open
            ? 'bg-white shadow-sm px-2 w-52'
            : 'hover:bg-gray-200 px-2 w-52'
        "
      >
        <HDLogo class="h-8 w-8 shrink-0 rounded" />
        <div
          class="flex flex-1 flex-col text-left duration-300 ease-in-out"
          :class="
            !sidebarStore.isExpanded
              ? 'opacity-0 ml-0 w-0 overflow-hidden'
              : 'opacity-100 ml-2 w-auto'
          "
        >
          <div class="text-base font-medium leading-none text-gray-900">
            Helpdesk
          </div>
          <div class="mt-1 text-sm leading-none text-gray-700">
            {{ authStore.userName }}
          </div>
        </div>
        <div
          class="duration-300 ease-in-out"
          :class="
            !sidebarStore.isExpanded
              ? 'opacity-0 ml-0 w-0 overflow-hidden'
              : 'opacity-100 ml-2 w-auto'
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
import { Dropdown } from "frappe-ui";
import { useAuthStore } from "@/stores/auth";
import { useSidebarStore } from "@/stores/sidebar";
import HDLogo from "@/components/icons/HDLogo.vue";

defineProps({
  options: {
    type: Array,
    required: true,
  },
});

const authStore = useAuthStore();
const sidebarStore = useSidebarStore();
</script>
