<template>
  <div v-if="!ticket.get?.loading" class="">
    <LayoutHeader>
      <template #left-header>
        <div class="flex flex-col">
          <Breadcrumbs :items="breadcrumbs" class="breadcrumbs">
            <template #prefix="{ item }">
              <Icon
                v-if="item.icon"
                :icon="item.icon"
                class="mr-1 h-4 flex items-center justify-center self-center"
              />
            </template>
          </Breadcrumbs>
          <TicketSLA />
        </div>
      </template>
      <template #right-header>
        <div class="flex gap-2 items-center">
          <MultipleAvatar
            :avatars="JSON.stringify(currentViewers)"
            size="md"
            :hide-name="true"
          />
          <!--  -->
          <div class="flex gap-1">
            <Button :icon="LucideChevronLeft" variant="ghost" />
            <Button
              :icon="LucideChevronRight"
              variant="ghost"
              @click="$socket.emit('fire')"
            />
          </div>
          <!--  -->
          <Dropdown :options="statusDropdown" placement="right">
            <template #default="{ open }">
              <Button :label="ticket.doc.status">
                <template #prefix>
                  <IndicatorIcon
                    :class="
                      ticketStatusStore.getStatus(ticket.doc.status)
                        ?.parsed_color
                    "
                  />
                </template>
              </Button>
            </template>
          </Dropdown>
          <!--  -->
          <Dropdown
            :placement="'right'"
            :options="[
              {
                label: 'Split Ticket',
              },
            ]"
          >
            <Button
              icon="more-horizontal"
              class="text-gray-600"
              variant="ghost"
            />
          </Dropdown>
        </div>
        <!-- <MultipleAvatar :avatars="assignedAgents" size="sm" /> -->
      </template>
    </LayoutHeader>
    <div class="h-full flex overflow-hidden">
      <div class="flex-1 flex flex-col">
        <!-- Tabs -->
        <TicketActivityPanel />
        <!-- Comm Area -->
        <!-- <CommunicationArea ref="communicationAreaRef" /> -->
      </div>

      <!-- Sidebar with Resizer -->
      <TicketSidebar />
    </div>
  </div>
</template>

<script setup lang="ts">
import { MultipleAvatar } from "@/components";
import { IndicatorIcon } from "@/components/icons";
import LayoutHeader from "@/components/LayoutHeader.vue";
import TicketActivityPanel from "@/components/ticket-agent/TicketActivityPanel.vue";
import TicketSidebar from "@/components/ticket-agent/TicketSidebar.vue";
import TicketSLA from "@/components/ticket-agent/TicketSLA.vue";
import { useTicket } from "@/composables/useTicket";
import { useView } from "@/composables/useView";
import { useAuthStore } from "@/stores/auth";
import { globalStore } from "@/stores/globalStore";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { TicketSymbol, View } from "@/types";
import { HDTicketStatus } from "@/types/doctypes";
import { getIcon } from "@/utils";
import { Breadcrumbs, Dropdown, toast } from "frappe-ui";
import {
  computed,
  ComputedRef,
  h,
  onMounted,
  onUnmounted,
  provide,
  ref,
} from "vue";
import { useRoute, useRouter } from "vue-router";

import LucideChevronLeft from "~icons/lucide/chevron-left";
import LucideChevronRight from "~icons/lucide/chevron-right";

const props = defineProps({
  ticketId: {
    type: String,
    required: true,
  },
});

const route = useRoute();
const router = useRouter();
const { $socket } = globalStore();
const { userId } = useAuthStore();

const ticket = useTicket(props.ticketId);
provide(
  TicketSymbol,
  computed(() => ticket)
);

const ticketStatusStore = useTicketStatusStore();
const { findView } = useView("HD Ticket");

const assignedAgents = computed(() => {
  return [];
  // if (ticket.doc?.assigned_to) {
  //   return JSON.stringify([ticket.doc?.assigned_to]);
  // }
  // return JSON.stringify([]);
});

const breadcrumbs = computed(() => {
  let items = [{ label: "Tickets", route: { name: "TicketsAgent" } }];
  if (route.query.view) {
    const currView: ComputedRef<View> = findView(route.query.view as string);
    if (currView) {
      items.push({
        label: currView.value?.label,
        icon: getIcon(currView.value?.icon),
        route: { name: "TicketsAgent", query: { view: currView.value?.name } },
      });
    }
  }
  items.push({
    label: ticket.doc?.subject,
    //   onClick: () => {
    //     showSubjectDialog.value = true;
    //   },
  });
  return items;
});

const statusDropdown = computed(() =>
  ticketStatusStore.statuses.data?.map((o: HDTicketStatus) => ({
    label: o.label_agent,
    value: o.label_agent,
    onClick: () =>
      ticket.setValue.submit(
        {
          status: o.label_agent,
        },
        {
          onSuccess: () => toast.success(__("Ticket updated")),
        }
      ),
    icon: () =>
      h(IndicatorIcon, {
        class: o.parsed_color,
      }),
  }))
);

const currentViewers = ref<string[]>([]);
const handleBeforeUnload = () => {
  // This will attempt to send the message, but may not always work
  // due to browser limitations on beforeunload
  $socket.emit("stop_view_ticket", props.ticketId);
};
onMounted(() => {
  // Listen for viewer updates
  $socket.on("ticket_viewers", (data) => {
    console.log("Received ticket viewers:", data);
    if (data.ticket_id === props.ticketId) {
      const viewers = JSON.parse(data.users).filter(
        (u: string) => u !== userId
      );
      currentViewers.value = viewers.length ? viewers : [];
    }

    window.addEventListener("beforeunload", handleBeforeUnload);
  });

  // Start viewing the ticket
  $socket.emit("view_ticket", props.ticketId);
});
onUnmounted(() => {
  // Stop viewing the ticket
  window.removeEventListener("beforeunload", handleBeforeUnload);
  $socket.emit("stop_view_ticket", props.ticketId);
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
