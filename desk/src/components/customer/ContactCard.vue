<template>
  <div
    class="min-w-96 max-w-96 rounded-md bg-surface-white border border-gray-200 px-3 py-2.5 flex flex-col gap-2.5"
  >
    <div class="flex items-center justify-between">
      <div class="flex gap-2 items-center min-w-0">
        <Avatar
          size="lg"
          :shape="'circle'"
          :image="contact.image ?? ''"
          :label="contact.contact_name"
        />
        <p
          class="truncate min-w-0"
          :class="contact.is_manager || contact.is_primary ? 'max-w-[50%]' : ''"
        >
          {{ contact.contact_name }}
        </p>
        <Badge v-if="contact.is_primary" label="Primary" theme="blue" />
        <Tooltip v-if="contact.is_manager" text="Manager" placement="top">
          <LucideBriefcase class="h-4 w-4 text-ink-gray-6" />
        </Tooltip>
      </div>
      <Dropdown placement="bottom-end" :options="dropdownOptions">
        <Button class="h-6 w-6 p-0" variant="ghost">
          <LucideMoreHorizontal class="h-4 w-4 text-ink-gray-6" />
        </Button>
      </Dropdown>
    </div>
    <div class="border-t border-gray-200 w-full" />
    <div class="flex flex-col gap-3">
      <template v-for="(item, index) in contactDetails" :key="index">
        <div
          class="flex items-center gap-2 text-sm text-ink-gray-8 font-[420]"
          :class="item.class?.(item.value)"
        >
          <component
            :is="item.icon"
            class="h-4 w-4 text-ink-gray-6"
            :class="item.color?.(item.value)"
          />
          <span
            class="text-ink-gray-8"
            :class="[item.class?.(item.value), item.color?.(item.value)]"
            >{{ item.value }}</span
          >
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { CustomerContact } from "@/types";
import { Avatar, Badge, Button, Dropdown, Tooltip, dayjs } from "frappe-ui";
import { computed, markRaw } from "vue";
import LucideBriefcase from "~icons/lucide/briefcase";
import LucideMail from "~icons/lucide/mail";
import LucideMoreHorizontal from "~icons/lucide/more-horizontal";
import LucidePhone from "~icons/lucide/phone";
import LucideRotateCW from "~icons/lucide/rotate-cw";
import LucideTicket from "~icons/lucide/ticket";

const props = defineProps<{
  contact: CustomerContact;
}>();

const ticketCountLabel = computed(() => {
  const count = props.contact.ticket_count;
  if (count === 0) return "No open tickets";
  return `${count} ${count === 1 ? "ticket" : "tickets"}`;
});

const contactDetails = computed(() => [
  {
    icon: markRaw(LucideMail),
    value: props.contact.email_id || "-",
  },
  {
    icon: markRaw(LucidePhone),
    value: props.contact.mobile_no || "-",
  },
  {
    icon: markRaw(LucideRotateCW),
    value: `Updated ${dayjs(props.contact.modified).fromNow()}`,
  },
  {
    icon: markRaw(LucideTicket),
    value: ticketCountLabel.value,
    color: (value: string) =>
      value !== "No open tickets" ? "!text-amber-700" : "!text-ink-gray-7",
    class: (value: string) =>
      value !== "No open tickets" ? "hover:underline cursor-pointer" : "",
  },
]);

const dropdownOptions = [
  {
    label: "Edit Contact",
    icon: "edit-2",
    onClick: () => console.log("Edit Contact"),
  },
  {
    label: "Delete Contact",
    icon: "trash-2",
    onClick: () => console.log("Delete Contact"),
  },
];
</script>

<style scoped></style>
