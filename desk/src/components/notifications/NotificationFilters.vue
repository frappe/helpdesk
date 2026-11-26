<template>
  <div class="flex items-center justify-between gap-2 px-4 py-2">
    <TabButtons v-model="notificationStore.readFilter" :options="readOptions" />
    <Dropdown :options="categoryOptions" align="end">
      <Button :label="category.label" :icon-left="category.icon">
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

const notificationStore = useNotificationStore();

const readOptions = [
  { label: __("All"), value: "all" },
  { label: __("Unread"), value: "unread" },
];

// Notification Log types helpdesk produces; core writes Mention and Assignment
const categories = [
  { label: __("All categories"), value: "", icon: "lucide-list" },
  { label: __("Mentions"), value: "Mention", icon: "lucide-at-sign" },
  { label: __("Assignments"), value: "Assignment", icon: "lucide-user-plus" },
  { label: __("Reactions"), value: "Reaction", icon: "lucide-smile-plus" },
  {
    label: __("Reopened tickets"),
    value: "Ticket Reopened",
    icon: "lucide-rotate-ccw",
  },
];
const categoryOptions = categories.map((c) => ({
  label: c.label,
  icon: c.icon,
  onClick: () => (notificationStore.category = c.value),
}));
const category = computed(
  () =>
    categories.find((c) => c.value === notificationStore.category) ??
    categories[0]
);
</script>
