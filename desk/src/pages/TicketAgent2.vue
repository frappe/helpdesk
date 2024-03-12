<template>
  <div class="flex flex-col">
    <LayoutHeader v-if="ticket.data">
      <template #left-header>
        <Breadcrumbs :items="breadcrumbs" />
      </template>
      <template #right-header>
        <component :is="ticket.data._assignedTo.length == 1 ? 'Button' : 'div'">
          <MultipleAvatar
            :avatars="ticket.data._assignedTo"
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
    <div v-if="ticket.data" class="flex h-full overflow-hidden">
      <Tabs v-slot="{ tab }" v-model="tabIndex" :tabs="tabs">
        <div
          class="flex items-center justify-between px-10 py-5 text-lg font-medium"
        >
          <div
            class="flex h-7 items-center text-xl font-semibold text-gray-800"
          >
            {{ tab.label }}
          </div>
        </div>
        <TicketsAgentList
          v-if="tab.label === 'Customer Tickets'"
          :rows="customerTickets?.data?.data"
          :columns="customerTickets?.data?.columns"
          :options="{
            selectable: false,
            pagination: false,
          }"
        />
        <Activities
          v-else
          :activities="activities"
          :type="tab.label === 'Emails' ? 'email' : 'all'"
        />
      </Tabs>
      <Sidebar />
    </div>
    <AssignmentModal
      v-if="ticket.data"
      v-model="showAssignmentModal"
      v-model:assignees="ticket.data._assignedTo"
      :doc="ticket.data"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, h } from "vue";
import {
  ActivityIcon,
  EmailIcon,
  IndicatorIcon,
  TicketIcon,
} from "@/components/icons";
import { Breadcrumbs, createResource, Dropdown, Tabs } from "frappe-ui";
import { Activities, Sidebar } from "@/components/ticket";
import { LayoutHeader, MultipleAvatar, AssignmentModal } from "@/components";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { createToast } from "@/utils";

const ticketStatusStore = useTicketStatusStore();

const tabIndex = ref(0);
const tabs = [
  {
    label: "Activity",
    icon: ActivityIcon,
  },
  {
    label: "Emails",
    icon: EmailIcon,
  },
  {
    label: "Customer Tickets",
    icon: TicketIcon,
  },
];

const customerTickets = ref([]);

const props = defineProps({
  ticketId: {
    type: String,
    required: true,
  },
});

const breadcrumbs = computed(() => {
  let items = [{ label: "Tickets", route: { name: "TicketsAgent" } }];
  items.push({
    label: ticket?.data?.subject,
    route: { name: "TicketAgent" },
  });

  return items;
});

const ticket = createResource({
  url: "helpdesk.helpdesk.doctype.hd_ticket.api.get_one",
  cache: ["Ticket", props.ticketId],
  auto: true,
  params: {
    name: props.ticketId,
  },
  transform(data) {
    data._assignedTo = [
      {
        name: data.assignee.email,
        image: data.assignee.image,
        label: data.assignee.name,
      },
    ];
    return data;
  },
  onSuccess(data) {
    customerTickets.value = createResource({
      url: "helpdesk.api.doc.get_list_data",
      params: {
        doctype: "HD Ticket",
        filters: {
          customer: ["=", data.customer],
        },
        columns: [
          { label: "Name", type: "Data", key: "name", width: "5rem" },
          { label: "Subject", type: "Data", key: "subject", width: "25rem" },
          { label: "Status", type: "Data", key: "status", width: "8rem" },
        ],
        rows: ["name", "subject", "status"],
      },
      auto: true,
      transform(data) {
        data.data.forEach((row) => {
          row.name = row.name.toString();
        });
      },
    });
  },
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

  const historyProps = [...ticket.data.history, ...ticket.data.views].map(
    (h) => {
      return {
        type: h.action ? "update" : "view",
        key: h.creation,
        content: h.action ? h.action : "viewed this",
        creation: h.creation,
        user: h.user.name + " ",
      };
    }
  );

  return [...emailProps, ...commentProps, ...historyProps].sort(
    (a, b) => new Date(a.creation) - new Date(b.creation)
  );
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
