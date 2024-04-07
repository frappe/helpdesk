<template>
  <div class="flex flex-col">
    <LayoutHeader v-if="ticket.data">
      <template #left-header>
        <Breadcrumbs :items="breadcrumbs" />
      </template>
      <template #right-header>
        <div v-if="ticketAgentStore.assignees.length">
          <component
            :is="ticketAgentStore.assignees.length == 1 ? 'Button' : 'div'"
          >
            <MultipleAvatar
              :avatars="ticketAgentStore.assignees"
              @click="showAssignmentModal = true"
            />
          </component>
        </div>
        <button
          v-else
          class="rounded bg-gray-100 px-2 py-1.5 text-base text-gray-800"
          @click="showAssignmentModal = true"
        >
          Assign
        </button>
        <Dropdown :options="dropdownOptions">
          <template #default="{ open }">
            <Button :label="ticket.data.status">
              <template #prefix>
                <IndicatorIcon
                  :class="ticketStatusStore.colorMap[ticket.data.status]"
                />
              </template>
              <template #suffix>
                <FeatherIcon
                  :name="open ? 'chevron-up' : 'chevron-down'"
                  class="h-4"
                />
              </template>
            </Button>
          </template>
        </Dropdown>
      </template>
    </LayoutHeader>
    <div v-if="ticket.data" class="flex h-screen overflow-hidden">
      <div class="flex flex-1 flex-col">
        <div
          class="pr-7.5 flex items-center justify-between border-b py-1 pl-10"
        >
          <span class="text-lg font-semibold">Activity</span>
          <Switch
            v-model="ticketAgentStore.showFullActivity"
            size="sm"
            label="Show all activity"
          />
        </div>
        <TicketAgentActivities :activities="ticketAgentStore.activities" />
        <CommunicationArea
          v-model="ticket.data"
          v-model:reload="reload_email"
        />
      </div>
      <TicketAgentSidebar :ticket="ticket.data" />
    </div>
    <AssignmentModal
      v-if="ticket.data"
      v-model="showAssignmentModal"
      :assignees="ticketAgentStore.assignees"
      @update="
        (data) => {
          ticketAgentStore.updateAssignees(data);
          // TODO: what if error? / async
          showAssignmentModal = false;
        }
      "
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, h } from "vue";
import { Breadcrumbs, Dropdown, Switch } from "frappe-ui";

import {
  LayoutHeader,
  MultipleAvatar,
  AssignmentModal,
  CommunicationArea,
} from "@/components";
import { TicketAgentActivities, TicketAgentSidebar } from "@/components/ticket";
import { IndicatorIcon } from "@/components/icons";

import { useTicketStatusStore } from "@/stores/ticketStatus";
import { useTicketAgentStore } from "@/stores/ticketAgent";

const ticketStatusStore = useTicketStatusStore();
const ticketAgentStore = useTicketAgentStore();

const props = defineProps({
  ticketId: {
    type: String,
    required: true,
  },
});

const reload_email = ref(false);
const showAssignmentModal = ref(false);
const ticket = ticketAgentStore.getTicket(props.ticketId);

const breadcrumbs = computed(() => {
  let items = [{ label: "Tickets", route: { name: "TicketsAgent" } }];
  items.push({
    label: ticket?.data?.subject,
    route: { name: "TicketAgent" },
  });

  return items;
});

const dropdownOptions = computed(() =>
  ticketStatusStore.options.map((o) => ({
    label: o,
    value: o,
    onClick: () => ticketAgentStore.updateTicket("status", o),
    icon: () =>
      h(IndicatorIcon, {
        class: ticketStatusStore.colorMap[o],
      }),
  }))
);
</script>
