<template>
  <Dropdown :options="options">
    <template #default="{ open }">
      <div
        class="-all flex w-max cursor-pointer items-center gap-2 rounded px-0.5 py-2"
        :class="{
          'hover:bg-gray-100': sidebarStore.isExpanded,
        }"
      >
        <Avatar
          size="md"
          :label="authStore.userName"
          :image="authStore.userImage"
        />
        <div
          class="flex shrink-0 items-center gap-2 text-gray-800 duration-300"
          :class="{
            'opacity-100': sidebarStore.isExpanded,
            'opacity-0': !sidebarStore.isExpanded,
            '-z-50': !sidebarStore.isExpanded,
          }"
        >
          <div class="text-base font-medium">
            {{ authStore.userName }}
          </div>
          <LucideChevronUp v-if="open" class="w-4 text-gray-700" />
          <LucideChevronDown v-else class="w-4 text-gray-700" />
        </div>
      </div>
    </template>
  </Dropdown>
</template>

<script setup lang="ts">
import { Avatar, Dropdown } from "frappe-ui";
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
