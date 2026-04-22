<template>
  <div
    class="md:mx-5 md:my-4 flex items-center justify-between text-lg font-medium mx-6 !mb-0 !my-3"
  >
    <div class="flex h-8 items-center text-xl font-semibold text-gray-800">
      {{ title }}
    </div>
    <Dropdown
      v-if="title == 'Calls'"
      :options="callActions"
      @click.stop
      placement="right"
    >
      <template v-slot="{ open }">
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
  </div>
  <CallLogModal
    v-model="showCallLogModal"
    :ticketId="ticketId"
    @after-insert="refreshTicket"
  />
</template>

<script setup lang="ts">
import { PhoneIcon } from "@/components/icons";
import CallLogModal from "@/pages/call-logs/CallLogModal.vue";
import { __ } from "@/translation";
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
const ticketId = inject<string>("ticketId");

const callActions = computed(() => {
  let actions = [
    {
      icon: h(PhoneIcon, { class: "h-4 w-4" }),
      label: __("Make a Call"),
      onClick: () => makeCall(),
    },
    {
      icon: "edit-3",
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
