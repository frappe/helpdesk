<template>
  <Dropdown :options="options">
    <template #default="{ open }">
      <div
        class="flex w-max cursor-pointer items-center gap-2 rounded-md px-1.5 py-2 transition-all"
        :class="{
          'hover:bg-gray-100': sidebarStore.isExpanded,
        }"
      >
        <Avatar
          size="sm"
          :label="authStore.userName"
          :image-u-r-l="authStore.userImage"
        />
        <div
          class="flex shrink-0 items-center gap-1 text-gray-800 duration-300"
          :class="{
            'opacity-100': sidebarStore.isExpanded,
            'opacity-0': !sidebarStore.isExpanded,
            '-z-50': !sidebarStore.isExpanded,
          }"
        >
          <div class="text-sm font-semibold">
            {{ authStore.userName }}
          </div>
          <FeatherIcon
            :name="open ? 'chevron-up' : 'chevron-down'"
            class="h-4 w-4 text-gray-600"
          />
        </div>
      </div>
    </template>
  </Dropdown>
</template>

<script setup lang="ts">
import { Avatar, Dropdown, FeatherIcon } from "frappe-ui";
import { useAuthStore } from "@/stores/auth";
import { useSidebarStore } from "@/stores/sidebar";

defineProps({
  options: {
    type: Array,
    required: true,
  },
});

const authStore = useAuthStore();
const sidebarStore = useSidebarStore();
</script>
