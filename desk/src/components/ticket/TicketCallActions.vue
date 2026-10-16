<template>
  <Dropdown :options="callActions" align="end">
    <template v-slot="{ open }">
      <Button variant="subtle" :label="__('New')">
        <template #prefix>
          <LucidePlus class="h-4 w-4" />
        </template>
        <template #suffix>
          <component
            :is="open ? LucideChevronUp : LucideChevronDown"
            class="h-4 w-4"
          />
        </template>
      </Button>
    </template>
  </Dropdown>
  <CallLogModal
    v-model="showCallLogModal"
    :ticketId="ticket.value?.name"
    @after-insert="refreshTicket"
  />
</template>

<script setup lang="ts">
import { PhoneIcon } from "@/components/icons";
import CallLogModal from "@/pages/call-logs/CallLogModal.vue";
import { __ } from "@/translation";
import { TicketSymbol } from "@/types";
import { Button, Dropdown } from "frappe-ui";
import { h, inject, ref } from "vue";
import LucideChevronDown from "~icons/lucide/chevron-down";
import LucideChevronUp from "~icons/lucide/chevron-up";
import LucidePlus from "~icons/lucide/plus";

const makeCall = inject<() => void>("makeCall");
const refreshTicket = inject<() => void>("refreshTicket");
const showCallLogModal = ref(false);
const ticket = inject(TicketSymbol)!;

const callActions = [
  {
    icon: h(PhoneIcon, { class: "h-4 w-4" }),
    label: __("Make a Call"),
    onClick: () => makeCall?.(),
  },
  {
    icon: "lucide-edit-3",
    label: __("Log a Call"),
    onClick: () => (showCallLogModal.value = true),
  },
];
</script>
