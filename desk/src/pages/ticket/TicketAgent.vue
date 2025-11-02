<template>
  <div class="flex flex-col">
    <LayoutHeader v-if="ticket.data">
      <template #left-header>
        <Breadcrumbs :items="breadcrumbs" class="breadcrumbs">
          <template #prefix="{ item }">
            <Icon
              v-if="item.icon"
              :icon="item.icon"
              class="mr-1 h-4 flex items-center justify-center self-center"
            />
          </template>
        </Breadcrumbs>
      </template>
      <template #right-header>
        <CustomActions
          v-if="ticket.data._customActions"
          :actions="ticket.data._customActions"
        />
        <div v-if="ticket.data.assignees?.length">
          <component :is="ticket.data.assignees.length == 1 ? 'Button' : 'div'">
            <MultipleAvatar
              :avatars="ticket.data.assignees"
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
                  :class="ticketStatusStore.textColorMap[ticket.data.status]"
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
    <div v-if="ticket.data" class="flex h-full overflow-hidden">
      <div class="flex flex-1 flex-col max-w-[calc(100%-382px)]">
        <!-- ticket activities -->
        <div class="overflow-y-hidden flex flex-1 !h-full flex-col">
          <Tabs v-model="tabIndex" :tabs="tabs">
            <TabList />
            <TabPanel v-slot="{ tab }" class="h-full">
              <TicketAgentActivities
                ref="ticketAgentActivitiesRef"
                :activities="filterActivities(tab.name)"
                :title="tab.label"
                :ticket-status="ticket.data?.status"
                @update="
                  () => {
                    ticket.reload();
                  }
                "
                @email:reply="
                  (e) => {
                    communicationAreaRef.replyToEmail(e);
                  }
                "
                @email:forward="
                  (e) => {
                    communicationAreaRef.forwardEmail(e);
                  }
                "
              />
            </TabPanel>
          </Tabs>
        </div>
        <CommunicationArea
          ref="communicationAreaRef"
          v-model="ticket.data"
          :to-emails="[ticket.data?.raised_by]"
          :cc-emails="[]"
          :bcc-emails="[]"
          :key="ticket.data?.name"
          @update="
            () => {
              ticket.reload();
              ticketAgentActivitiesRef.scrollToLatestActivity();
            }
          "
        />
      </div>

      <!-- Sidepanel with Resizer -->
      <TicketSidebar />
    </div>
    <SetContactPhoneModal
      v-model="showPhoneModal"
      :name="ticket.data?.contact?.name"
      @onUpdate="ticket.reload"
    />
  </div>
</template>

<script setup lang="ts">
import TicketActivityPanel from "@/components/ticket-agent/TicketActivityPanel.vue";
import TicketHeader from "@/components/ticket-agent/TicketHeader.vue";
import TicketSidebar from "@/components/ticket-agent/TicketSidebar.vue";
import SetContactPhoneModal from "@/components/ticket/SetContactPhoneModal.vue";
import { useActiveViewers } from "@/composables/realtime";
import { useTicket } from "@/composables/useTicket";
import { ticketsToNavigate } from "@/composables/useTicketNavigation";
import { globalStore } from "@/stores/globalStore";
import { useTelephonyStore } from "@/stores/telephony";
import {
  ActivitiesSymbol,
  AssigneeSymbol,
  Customizations,
  CustomizationSymbol,
  RecentSimilarTicketsSymbol,
  Resource,
  TicketContactSymbol,
  TicketSymbol,
} from "@/types";
import { createResource, toast, usePageMeta } from "frappe-ui";
import { computed, onBeforeUnmount, onMounted, provide, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { showCommentBox, showEmailBox } from "./modalStates";

const telephonyStore = useTelephonyStore();
const { $socket } = globalStore();

const props = defineProps({
  ticketId: {
    type: String,
    required: true,
  },
});
const route = useRoute();
const showPhoneModal = ref(false);

const ticketComposable = computed(() => useTicket(props.ticketId));
const ticket = computed(() => ticketComposable.value.ticket);
const customizations: Resource<Customizations> = createResource({
  url: "helpdesk.helpdesk.doctype.hd_ticket.api.get_ticket_customizations",
  cache: ["HD Ticket", "customizations"],
  auto: true,
});

provide(TicketSymbol, ticket);

provide(
  AssigneeSymbol,
  computed(() => ticketComposable.value.assignees)
);
provide(
  TicketContactSymbol,
  computed(() => ticketComposable.value.contact)
);
provide(
  CustomizationSymbol,
  computed(() => customizations)
);
provide(
  RecentSimilarTicketsSymbol,
  computed(() => ticketComposable.value.recentSimilarTickets)
);
provide(
  ActivitiesSymbol,
  computed(() => ticketComposable.value.activities)
);
provide("makeCall", () => {
  if (
    !ticketComposable.value.contact.data?.mobile_no &&
    !ticketComposable.value.contact.data?.phone
  ) {
    showPhoneModal.value = true;
    return;
  }
  telephonyStore.makeCall({
    number:
      ticketComposable.value.contact.data?.phone ||
      ticketComposable.value.contact.data?.mobile_no,
    doctype: "HD Ticket",
    docname: props.ticketId,
  });
});
const viewerComposable = computed(() => useActiveViewers(ticket.value.name));
const viewers = computed(
  () => viewerComposable.value.currentViewers[props.ticketId] || []
);
const { startViewing, stopViewing } = viewerComposable.value;

// handling for faster navigation between tickets
watch(
  () => route.params.ticketId,
  (newTicketId, oldTicketId) => {
    if (newTicketId === oldTicketId) return;

    if (oldTicketId) stopViewing(oldTicketId as string);
    startViewing(newTicketId as string);
  },
  { immediate: true }
);

type TicketUpdateData = {
  ticket_id: string;
  user: string;
  field: string;
  value: string;
};

onMounted(() => {
  ticketsToNavigate.update({
    params: {
      ticket: props.ticketId,
      current_view: route.query.view as string,
    },
  });
  ticketsToNavigate.reload();
  ticket.value.markSeen.reload();

  $socket.on("ticket_update", (data: TicketUpdateData) => {
    if (data.ticket_id === ticket.value?.name) {
      // Notify the user about the update
      toast.info(`User ${data.user} updated ${data.field} to ${data.value}`);
    }
  });
});

onBeforeUnmount(() => {
  stopViewing(props.ticketId);
  showEmailBox.value = false;
  showCommentBox.value = false;
});

usePageMeta(() => {
  return {
    title: props.ticketId,
  };
});
</script>

<style>
.breadcrumbs button {
  background-color: inherit !important;
  &:hover,
  &:focus {
    background-color: inherit !important;
  }
}
</style>
