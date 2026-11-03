<template>
  <div class="flex items-center justify-between gap-2 px-4 py-2">
    <TabButtons v-model="notificationStore.readFilter" :options="readOptions" />
    <Dropdown :options="categoryOptions" align="end">
      <Button :label="categoryLabel">
        <template #prefix>
          <LucideList class="h-4 w-4" />
        </template>
        <template #suffix>
          <LucideChevronDown class="h-4 w-4" />
        </template>
      </Button>
    </Dropdown>
  </div>
</template>

<script setup lang="ts">
import { useNotificationStore } from "@/stores/notification";
import { __ } from "@/translation";
import { Button, Dropdown, TabButtons } from "frappe-ui";
import { computed } from "vue";
import LucideChevronDown from "~icons/lucide/chevron-down";
import LucideList from "~icons/lucide/list";

const notificationStore = useNotificationStore();

const readOptions = [
  { label: __("All"), value: "all" },
  { label: __("Unread"), value: "unread" },
];

// Notification Log types helpdesk produces; core writes Mention and Assignment
const categories = [
  { label: __("All categories"), value: "" },
  { label: __("Mentions"), value: "Mention" },
  { label: __("Assignments"), value: "Assignment" },
  { label: __("Reactions"), value: "Reaction" },
  { label: __("Reopened tickets"), value: "Ticket Reopened" },
];
const categoryOptions = categories.map((c) => ({
  label: c.label,
  onClick: () => (notificationStore.category = c.value),
}));
const categoryLabel = computed(
  () => categories.find((c) => c.value === notificationStore.category)?.label
);
</script>
