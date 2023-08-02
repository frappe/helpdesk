<template>
  <div class="flex flex-col">
    <div class="border-l">
      <div class="m-4 text-base">
        <div class="flex items-center justify-between">
          <div class="text-lg font-semibold text-gray-900">Ticket details</div>
          <Button
            icon="x"
            theme="gray"
            variant="ghost"
            @click="ticketStore.sidebar.isExpanded = false"
          />
        </div>
        <div class="my-6 flex flex-col justify-between gap-3.5">
          <div v-if="data.customer" class="flex justify-between">
            <div class="text-gray-600">Customer:</div>
            <div class="font-medium text-gray-700">
              {{ data.customer }}
            </div>
          </div>
          <div class="flex justify-between">
            <div class="text-gray-600">First Response Due:</div>
            <div class="font-medium text-gray-700">
              {{ dayjs(data.response_by).format(dateFormat) }}
            </div>
          </div>
          <div class="flex items-center justify-between">
            <div class="text-gray-600">Resolution Due:</div>
            <div class="font-medium text-gray-700">
              <span v-if="data.resolution_by">
                {{ dayjs(data.resolution_by).format(dateFormat) }}
              </span>
              <Badge
                v-else
                label="Paused"
                size="md"
                variant="subtle"
                theme="green"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="divider"></div>
    <div
      class="flex grow flex-col gap-3 truncate border-l p-4"
      :style="{
        'overflow-y': 'scroll',
      }"
    >
      <div class="flex flex-col gap-1">
        <div class="text-xs text-gray-600">Assigned To</div>
        <Autocomplete
          placeholder="Select an agent"
          :options="agentStore.dropdown"
          :value="assignedTo"
          @change="assignAgent($event.value)"
        />
      </div>
      <div v-for="o in options" :key="o.field" class="flex flex-col gap-1">
        <div class="text-xs text-gray-600">
          {{ o.label }}
        </div>
        <Autocomplete
          :options="o.store.dropdown"
          :placeholder="`Select a ${o.label}`"
          :value="data[o.field]"
          @change="update(o.field, $event.value)"
        />
      </div>
      <CustomFields
        :template="data.template"
        :values="data.custom_fields"
        @change="updateCustomField"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { emitter } from "@/emitter";
import { useAgentStore } from "@/stores/agent";
import { useTeamStore } from "@/stores/team";
import { useTicketPriorityStore } from "@/stores/ticketPriority";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { useTicketTypeStore } from "@/stores/ticketType";
import { useUserStore } from "@/stores/user";
import { createToast } from "@/utils/toasts";
import dayjs from "dayjs";
import { Autocomplete, Button, createResource, call } from "frappe-ui";
import { computed } from "vue";
import CustomFields from "./CustomFields.vue";
import { useTicket, useTicketStore } from "./data";

const dateFormat = "MMM D, h:mm A";
const agentStore = useAgentStore();
const userStore = useUserStore();
const ticketStore = useTicketStore();
const ticket = useTicket();
const data = computed(() => ticket.value.data);

const assignedTo = computed(() => {
  const assignJson = JSON.parse(data.value._assign);
  const arr = Array.isArray(assignJson) ? assignJson : [];
  const user = arr.slice(-1).pop();
  const name = userStore.getUser(user)?.full_name || user;
  return name;
});

const options = computed(() => [
  {
    field: "ticket_type",
    label: "Ticket type",
    store: useTicketTypeStore(),
  },
  {
    field: "status",
    label: "Status",
    store: useTicketStatusStore(),
  },
  {
    field: "priority",
    label: "Priority",
    store: useTicketPriorityStore(),
  },
  {
    field: "agent_group",
    label: "Team",
    store: useTeamStore(),
  },
]);

function assignAgent(agent: string) {
  createResource({
    url: "run_doc_method",
    params: {
      dt: "HD Ticket",
      dn: data.value.name,
      method: "assign_agent",
      args: {
        agent,
      },
    },
    auto: true,
    onSuccess: () => {
      emitter.emit("update:ticket");
      createToast({
        title: `Ticket assigned to ${agent}`,
        icon: "check",
        iconClasses: "text-green-600",
      });
    },
  });
}

function update(fieldname: string, value: string) {
  createResource({
    url: "frappe.client.set_value",
    params: {
      doctype: "HD Ticket",
      name: data.value.name,
      fieldname,
      value,
    },
    auto: true,
    onSuccess: () => {
      emitter.emit("update:ticket");
      createToast({
        title: "Ticket updated",
        icon: "check",
        iconClasses: "text-green-600",
      });
    },
  });
}

function updateCustomField({ fieldname, value }) {
  call("helpdesk.helpdesk.doctype.hd_ticket.api.update_custom_field", {
    ticket_name: data.value.name,
    fieldname,
    value,
  }).then(() => {
    emitter.emit("update:ticket");
    createToast({
      title: "Ticket updated",
      icon: "check",
      iconClasses: "text-green-600",
    });
  });
}
</script>

<style scoped>
.divider {
  border-bottom: 1px solid #e2e2e2;
  border-style: dashed;
  position: relative;
}

.divider:before {
  position: absolute;
  bottom: -14px;
  left: 0;
  height: 28px;
  width: 14px;
  background: white;
  content: "";
  border-top-right-radius: 9999px;
  border-bottom-right-radius: 9999px;
  border-right-width: 1px;
  border-top-width: 1px;
  border-bottom-width: 1px;
}

.divider:after {
  position: absolute;
  bottom: -14px;
  left: 0;
  height: 28px;
  width: 14px;
  background: white;
  content: "";
  border-top-left-radius: 9999px;
  border-bottom-left-radius: 9999px;
  border-left-width: 1px;
  border-top-width: 1px;
  border-bottom-width: 1px;
}

.divider:after {
  right: 0;
  left: auto;
}
</style>
