<template>
  <div
    class="md:mx-5 md:my-4 flex items-center justify-between text-lg font-medium mx-6 !mb-0 !my-3"
  >
    <div class="flex h-8 items-center text-xl font-semibold text-ink-gray-8">
      {{ title }}
    </div>

    <!-- Calls dropdown -->
    <Dropdown
      v-if="title === __('Calls')"
      :options="callActions"
      @click.stop
      placement="right"
    >
      <template #default="{ open }">
        <Button variant="subtle" class="flex items-center gap-1">
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

    <!-- Tasks button -->
    <Button
      v-else-if="title === __('Tasks')"
      variant="subtle"
      @click="emit('new-task')"
    >
      <template #prefix>
        <FeatherIcon name="plus" class="h-4 w-4" />
      </template>
      {{ __("New") }}
    </Button>

    <!-- Emails button -->
    <Button
      v-else-if="title === __('Emails')"
      variant="subtle"
      @click="emit('new-email')"
    >
      <template #prefix>
        <FeatherIcon name="plus" class="h-4 w-4" />
      </template>
      {{ __("New") }}
    </Button>
  </div>

  <CallLogModal
    v-model="showCallLogModal"
    :ticketId="String(ticket?.doc?.name)"
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

const emit = defineEmits(["new-task", "new-email"]);

const makeCall = inject<() => void>("makeCall");
const refreshTicket = inject<() => void>("refreshTicket");
const ticket = inject(TicketSymbol);
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