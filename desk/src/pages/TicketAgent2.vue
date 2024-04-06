<template>
  <div class="flex flex-col">
    <LayoutHeader v-if="ticket.data">
      <template #left-header>
        <Breadcrumbs :items="breadcrumbs" />
      </template>
      <template #right-header>
        <component
          :is="ticketAgentStore.getAssignees().length == 1 ? 'Button' : 'div'"
        >
          <MultipleAvatar
            :avatars="ticketAgentStore.getAssignees()"
            @click="showAssignmentModal = true"
          />
        </component>
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
            v-model="showFullActivity"
            size="sm"
            label="Show all activity"
          />
        </div>
        <TicketAgentActivities :activities="activities" />
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
      :assignees="ticketAgentStore.getAssignees()"
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
import { Breadcrumbs, createResource, Dropdown, Switch } from "frappe-ui";

import { useTicketStatusStore } from "@/stores/ticketStatus";
import { useTicketAgentStore } from "@/stores/ticketAgent";
import { createToast } from "@/utils";

import {
  LayoutHeader,
  MultipleAvatar,
  AssignmentModal,
  CommunicationArea,
} from "@/components";

import { TicketAgentActivities, TicketAgentSidebar } from "@/components/ticket";

import { IndicatorIcon } from "@/components/icons";

const ticketStatusStore = useTicketStatusStore();
const ticketAgentStore = useTicketAgentStore();

const showFullActivity = ref(true);

const reload_email = ref(false);

const props = defineProps({
  ticketId: {
    type: String,
    required: true,
  },
});

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
    onClick: () => setValue.submit({ field: "status", value: o }),
    icon: () =>
      h(IndicatorIcon, {
        class: ticketStatusStore.colorMap[o],
      }),
  }))
);

const activities = computed(() => {
  const emailProps = ticket.data.communications.map((email) => {
    return {
      type: "email",
      key: email.creation,
      sender: { name: email.user.email, full_name: email.user.name },
      to: email.recipients,
      cc: email.cc,
      bcc: email.bcc,
      creation: email.creation,
      subject: email.subject,
      attachments: email.attachments,
      content: email.content,
    };
  });

  const commentProps = ticket.data.comments.map((comment) => {
    return {
      type: "comment",
      key: comment.creation,
      commenter: comment.user.name,
      creation: comment.creation,
      content: comment.content,
    };
  });

  if (!showFullActivity.value) {
    return [...emailProps, ...commentProps].sort(
      (a, b) => new Date(a.creation) - new Date(b.creation)
    );
  }

  const historyProps = [...ticket.data.history, ...ticket.data.views].map(
    (h) => {
      return {
        type: "history",
        key: h.creation,
        content: h.action ? h.action : "viewed this",
        creation: h.creation,
        user: h.user.name + " ",
      };
    }
  );

  const sorted = [...emailProps, ...commentProps, ...historyProps].sort(
    (a, b) => new Date(a.creation) - new Date(b.creation)
  );

  let data = [];
  let i = 0;

  while (i < sorted.length) {
    let currentActivity = sorted[i];
    if (currentActivity.type === "history") {
      currentActivity.relatedActivities = [];
      for (let j = i + 1; j < sorted.length; j++) {
        let nextActivity = sorted[j];
        if (nextActivity.type === "history") {
          currentActivity.relatedActivities.push(nextActivity);
        } else {
          data.push(currentActivity);
          i = j - 1;
          break;
        }
      }
    } else {
      data.push(currentActivity);
    }
    i++;
  }

  return data;
});

const showAssignmentModal = ref(false);

const setValue = createResource({
  url: "frappe.client.set_value",
  auto: false,
  makeParams: (params) => ({
    doctype: "HD Ticket",
    name: ticket.data.name,
    fieldname: params.field,
    value: params.value,
  }),
  onSuccess: () => {
    createToast({
      title: "Ticket updated",
      icon: "check",
      iconClasses: "text-green-600",
    });
  },
  // onError: useError(),
});
</script>
