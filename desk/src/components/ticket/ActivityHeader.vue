<template>
  <div
    class="flex items-center justify-between text-lg font-medium px-6 py-3 border-b border-border-gray-100 bg-white"
  >
    <div class="flex h-8 items-center text-lg font-bold text-ink-gray-9">
      {{ title }}
    </div>

    <div class="flex items-center">
      <Dropdown
        v-if="title === __('Calls')"
        :options="callActions"
        @click.stop
        placement="right"
      >
        <template #default="{ open }">
          <Button variant="solid" class="hd-black-button flex items-center gap-1">
            <template #prefix>
              <FeatherIcon name="plus" class="h-4 w-4" />
            </template>
            <span>{{ __("New") }}</span>
            <template #suffix>
              <FeatherIcon
                :name="open ? 'chevron-up' : 'chevron-down'"
                class="h-4 w-4"
              />
            </template>
          </Button>
        </template>
      </Dropdown>

      <Button
        v-else-if="title === __('Tasks')"
        variant="solid"
        class="hd-black-button"
        @click="emit('new-task')"
      >
        <template #prefix>
          <FeatherIcon name="plus" class="h-4 w-4" />
        </template>
        {{ __("New") }}
      </Button>
    </div>
  </div>

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
import { Button, Dropdown, FeatherIcon } from "frappe-ui";
import { computed, h, inject, ref } from "vue";

defineProps({
  title: {
    type: String,
    required: true,
  },
});

const emit = defineEmits(["new-task"]);
const makeCall = inject<() => void>("makeCall");
const refreshTicket = inject<() => void>("refreshTicket");
const ticket = inject<any>(TicketSymbol);
const showCallLogModal = ref(false);

const callActions = computed(() => [
  {
    icon: h(PhoneIcon, { class: "h-4 w-4" }),
    label: __("Make a Call"),
    onClick: () => makeCall?.(),
  },
  {
    icon: "edit-3",
    label: __("Log a Call"),
    onClick: () => {
      showCallLogModal.value = true;
    },
  },
]);
</script>
