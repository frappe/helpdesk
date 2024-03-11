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
        <Activities v-model="ticket" :title="tab.label" />
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
import { ActivityIcon, EmailIcon } from "@/components/icons";
import { Breadcrumbs, createResource, Dropdown, Tabs } from "frappe-ui";
import { Activities, Sidebar } from "@/components/ticket";
import { LayoutHeader, MultipleAvatar, AssignmentModal } from "@/components";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import IndicatorIcon from "@/components/icons/IndicatorIcon.vue";
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
];

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
