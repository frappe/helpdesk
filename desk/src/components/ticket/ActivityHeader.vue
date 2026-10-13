<template>
  <div
    class="md:mx-5 md:my-4 flex items-center justify-between text-md-medium mx-6 !mb-0 !my-3"
  >
    <div class="flex h-8 items-center text-xl-semibold text-ink-gray-8">
      {{ title }}
    </div>
    <Dropdown
      v-if="title == 'Calls'"
      :options="callActions"
      @click.stop
      align="end"
    >
      <template v-slot="{ open }">
        <Button variant="subtle" class="flex items-center gap-1">
          <template #prefix>
            <LucidePlus class="h-4 w-4" />
          </template>
          <span>{{ __("New") }}</span>
          <template #suffix>
            <component
              :is="open ? LucideChevronUp : LucideChevronDown"
              class="h-4 w-4"
            />
          </template>
        </Button>
      </template>
    </Dropdown>
  </div>
  <CallLogModal
    v-model="showCallLogModal"
    :ticketId="ticket.value?.name"
    @after-insert="refreshTicket"
  />
</template>

<script setup lang="ts">
import LucideChevronUp from "~icons/lucide/chevron-up";
import LucideChevronDown from "~icons/lucide/chevron-down";
import LucidePlus from "~icons/lucide/plus";
import { PhoneIcon } from "@/components/icons";
import CallLogModal from "@/pages/call-logs/CallLogModal.vue";
import { __ } from "@/translation";
import { TicketSymbol } from "@/types";
import { Dropdown } from "frappe-ui";
import { computed, h, inject, ref } from "vue";
defineProps({
  title: {
    type: String,
    required: true,
  },
});

const makeCall = inject<() => void>("makeCall");
const refreshTicket = inject<() => void>("refreshTicket");
const showCallLogModal = ref(false);
const ticket = inject(TicketSymbol)!;

const callActions = computed(() => {
  let actions = [
    {
      icon: h(PhoneIcon, { class: "h-4 w-4" }),
      label: __("Make a Call"),
      onClick: () => makeCall(),
    },
    {
      icon: "lucide-edit-3",
      label: __("Log a Call"),
      onClick: () => {
        showCallLogModal.value = true;
      },
    },
  ];
  return actions;
});
</script>

<style scoped></style>
