<template>
  <div class="flex flex-col">
    <LayoutHeader v-if="ticket.data">
      <template #left-header>
        <Breadcrumbs :items="breadcrumbs" />
      </template>
      <template #right-header>
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
        <div class="flex items-center justify-between border-b py-1 pr-2.5">
          <span class="pl-6 text-lg font-semibold">Activity</span>
          <Switch
            v-model="showFullActivity"
            size="sm"
            label="Show all activity"
          />
        </div>
        <TicketAgentActivities
          ref="ticketAgentActivitiesRef"
          :activities="activities"
          @email:reply="
            (e) => {
              communicationAreaRef.replyToEmail(e);
            }
          "
        />
        <CommunicationArea
          ref="communicationAreaRef"
          v-model="ticket.data"
          :to-emails="[ticket.data.raised_by]"
          :cc-emails="[]"
          :bcc-emails="[]"
          @update="
            () => {
              ticket.reload();
              ticketAgentActivitiesRef.scrollToLatestActivity();
            }
          "
        />
      </div>
      <TicketAgentSidebar
        :ticket="ticket.data"
        @update="({ field, value }) => updateTicket(field, value)"
        @email:open="(e) => communicationAreaRef.replyToEmail(null, e)"
      />
    </div>
    <AssignmentModal
      v-if="ticket.data"
      v-model="showAssignmentModal"
      :assignees="ticket.data.assignees"
      :docname="ticketId"
      doctype="HD Ticket"
      @update="
        () => {
          ticket.reload();
        }
      "
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, h } from "vue";
import { Breadcrumbs, Dropdown, Switch, createResource } from "frappe-ui";

import {
  LayoutHeader,
  MultipleAvatar,
  AssignmentModal,
  CommunicationArea,
} from "@/components";
import { TicketAgentActivities, TicketAgentSidebar } from "@/components/ticket";
import { IndicatorIcon } from "@/components/icons";

import { useTicketStatusStore } from "@/stores/ticketStatus";
import { useUserStore } from "@/stores/user";
import { createToast } from "@/utils";

const ticketStatusStore = useTicketStatusStore();
const { getUser } = useUserStore();
const ticketAgentActivitiesRef = ref(null);
const communicationAreaRef = ref(null);

const props = defineProps({
  ticketId: {
    type: String,
    required: true,
  },
});

const showFullActivity = ref(true);
const showAssignmentModal = ref(false);
const ticket = createResource({
  url: "helpdesk.helpdesk.doctype.hd_ticket.api.get_one",
  cache: ["Ticket", props.ticketId],
  auto: true,
  params: {
    name: props.ticketId,
  },
  transform: (data) => {
    if (data._assign) {
      data.assignees = JSON.parse(data._assign).map((assignee) => {
        return {
          name: assignee,
          image: getUser(assignee).user_image,
          label: getUser(assignee).full_name,
        };
      });
    }
  },
});

const breadcrumbs = computed(() => {
  let items = [{ label: "Tickets", route: { name: "TicketsAgent" } }];
  items.push({
    label: ticket.data?.subject,
    route: { name: "TicketAgent" },
  });

  return items;
});

const dropdownOptions = computed(() =>
  ticketStatusStore.options.map((o) => ({
    label: o,
    value: o,
    onClick: () => updateTicket("status", o),
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

  const data = [];
  let i = 0;

  while (i < sorted.length) {
    const currentActivity = sorted[i];
    if (currentActivity.type === "history") {
      currentActivity.relatedActivities = [];
      for (let j = i + 1; j < sorted.length; j++) {
        const nextActivity = sorted[j];
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

function updateTicket(fieldname: string, value: string) {
  createResource({
    url: "frappe.client.set_value",
    params: {
      doctype: "HD Ticket",
      name: props.ticketId,
      fieldname,
      value,
    },
    auto: true,
    onSuccess: () => {
      ticket.reload();
      createToast({
        title: "Ticket updated",
        icon: "check",
        iconClasses: "text-green-600",
      });
    },
    onError: () => {
      createToast({
        title: "Failed to update ticket",
        icon: "x",
        iconClasses: "text-red-600",
      });
    },
  });
}
</script>
