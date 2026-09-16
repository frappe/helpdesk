<template>
  <Dropdown :options="options" :offset="4" placement="bottom-start">
    <template #default="{ open }">
      <button
        type="button"
        class="group flex cursor-pointer items-center gap-1 rounded-md bg-transparent p-0.5"
        aria-label="Menu"
      >
        <img
          v-if="logo"
          :src="logo"
          alt=""
          aria-hidden="true"
          class="size-8 shrink-0 object-contain"
        />
        <span v-else class="size-8 shrink-0" />
        <FeatherIcon
          :name="open ? 'chevron-up' : 'chevron-down'"
          class="size-4 shrink-0 transition-colors duration-150 group-hover:text-ink-gray-9"
          :class="open ? 'text-ink-gray-9' : 'text-ink-gray-5'"
        />
      </button>
    </template>
  </Dropdown>
</template>

<script setup lang="ts">
// Menu and trigger together: a trigger has to read its menu's state, and only the slot
// knows it. The chevron alone answers the pointer — no fill behind the brand mark.
import { computed } from "vue";
import { Dropdown, FeatherIcon } from "frappe-ui";
import { useSession } from "@app/stores/session";

defineProps<{ options?: unknown[] }>();

// The favicon is the helpdesk's fallback everywhere else, so the topbar falls back with it.
const { config } = useSession();
const logo = computed(
  () => config.value?.brand_logo || config.value?.favicon || ""
);
</script>
