<template>
  <div class="flex flex-col border-l">
    <span>
      <TicketSidebarHeader title="Contact" />
      <div
        v-if="contact.full_name"
        class="flex items-center gap-3 border-b py-6"
      >
        <Avatar :image="contact.image" :label="contact.full_name" size="lg" />
        <div class="flex flex-col">
          <div class="text-lg font-semibold text-gray-800">
            {{ contact.full_name }}
          </div>
          <div class="text-base text-gray-600">
            {{ contact.company_name }}
          </div>
        </div>
      </div>
    </span>
    <div class="overflow-auto px-5">
      <div
        v-if="!isEmpty(contactOptions)"
        class="flex flex-col gap-3.5 border-b py-6 text-base"
      >
        <div
          v-for="c in contactOptions"
          :key="c.name"
          class="flex items-center gap-2"
        >
          <component :is="c.icon" class="w-4 text-gray-700" />
          <span class="text-gray-900">{{ c.value }}</span>
        </div>
      </div>
      <TicketContactTickets />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, inject } from "vue";
import { Avatar } from "frappe-ui";
import { isEmpty } from "lodash";
import TicketContactTickets from "./TicketContactTickets.vue";
import TicketSidebarHeader from "./TicketSidebarHeader.vue";
import { ITicket } from "./symbols";
import LucideMail from "~icons/lucide/mail";
import LucidePhone from "~icons/lucide/phone";
import LucideSmartphone from "~icons/lucide/smartphone";

const fields = [
  {
    field: "email_id",
    icon: LucideMail,
  },
  {
    field: "phone",
    icon: LucidePhone,
  },
  {
    field: "mobile_no",
    icon: LucideSmartphone,
  },
];

const ticket = inject(ITicket);
const contact = computed(() => ticket.data.contact);
const contactOptions = computed(() =>
  fields
    .map((o) => ({
      name: o.field,
      value: contact.value[o.field],
      icon: o.icon,
    }))
    .filter((o) => o.value)
);
</script>
