<template>
  <div class="flex flex-col">
    <div class="border-l">
      <span>
        <TicketSidebarHeader title="Details" />
        <div class="mx-5 my-6 flex flex-col justify-between gap-3.5 text-base">
          <div class="space-y-1.5">
            <span class="block text-sm text-gray-700">ID</span>
            <span class="block break-words font-medium text-gray-900">
              {{ data.name }}
            </span>
          </div>
          <div v-if="data.customer" class="space-y-1.5">
            <span class="block text-sm text-gray-700">Customer</span>
            <span class="block break-words font-medium text-gray-900">
              {{ data.customer }}
            </span>
          </div>
          <div
            v-if="data.first_responded_on || data.response_by"
            class="space-y-1.5"
          >
            <div class="text-sm text-gray-700">First response</div>
            <div class="mr-2 inline-block font-medium text-gray-900">
              {{ dayjs(data.first_responded_on || data.response_by).short() }}
            </div>
            <span v-if="data.response_by">
              <Badge
                v-if="!data.first_responded_on"
                label="Due"
                theme="orange"
                variant="outline"
              />
              <Badge
                v-else-if="
                  dayjs(data.first_responded_on).isBefore(
                    dayjs(data.response_by)
                  )
                "
                label="Fulfilled"
                theme="green"
                variant="outline"
              />
              <Badge v-else label="Failed" theme="red" variant="outline" />
            </span>
          </div>
          <div
            v-if="data.resolution_date || data.resolution_by"
            class="space-y-1.5"
          >
            <span class="block text-sm text-gray-700">Resolution</span>
            <span class="mr-2 font-medium text-gray-900">
              {{ dayjs(data.resolution_date || data.resolution_by).short() }}
            </span>
            <Badge
              v-if="
                dayjs(data.resolution_date || undefined).isAfter(
                  data.resolution_by
                )
              "
              label="Failed"
              theme="red"
              variant="outline"
            />
            <Badge
              v-else-if="!data.resolution_date"
              label="Due"
              theme="orange"
              variant="outline"
            />
            <Badge
              v-else-if="
                dayjs(data.resolution_date).isBefore(data.resolution_by)
              "
              label="Fulfilled"
              theme="green"
              variant="outline"
            />
          </div>
          <div class="space-y-1.5">
            <span class="block text-sm text-gray-700">Modified</span>
            <Tooltip :text="dayjs(ticket.data.modified).long()">
              <span class="block break-words font-medium text-gray-900">
                {{ dayjs(ticket.data.modified).fromNow() }}
              </span>
            </Tooltip>
          </div>
          <div class="space-y-1.5">
            <span class="block text-sm text-gray-700">Source</span>
            <span class="block break-words font-medium text-gray-900">
              {{ ticket.data.via_customer_portal ? "Portal" : "Mail" }}
            </span>
          </div>
          <div v-if="data.feedback_rating" class="space-y-1.5">
            <span class="block text-sm text-gray-700">Feedback</span>
            <StarRating :rating="data.feedback_rating" />
            <span class="block font-medium text-gray-900">
              {{ data.feedback_text }}
            </span>
            <span class="block text-gray-900">
              {{ data.feedback_extra }}
            </span>
          </div>
        </div>
      </span>
    </div>
    <div class="divider"></div>
    <div
      class="flex grow flex-col gap-3 truncate border-l p-5"
      :style="{
        'overflow-y': 'scroll',
      }"
    >
      <div v-for="o in options" :key="o.field" class="space-y-1.5">
        <span class="block text-sm text-gray-700">
          {{ o.label }}
        </span>
        <Autocomplete
          :options="o.store.dropdown"
          :placeholder="`Select a ${o.label}`"
          :value="data[o.field]"
          @change="update(o.field, $event.value)"
        />
      </div>
      <UniInput
        v-for="field in data.template.fields"
        :key="field.fieldname"
        :field="field"
        :value="data[field.fieldname]"
        @change="update(field.fieldname, $event.value)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, inject } from "vue";
import { createResource, Autocomplete, Tooltip } from "frappe-ui";
import { dayjs } from "@/dayjs";
import { emitter } from "@/emitter";
import { createToast } from "@/utils";
import { useTeamStore } from "@/stores/team";
import { useTicketPriorityStore } from "@/stores/ticketPriority";
import { useTicketTypeStore } from "@/stores/ticketType";
import { useError } from "@/composables/error";
import { StarRating, UniInput } from "@/components";
import TicketSidebarHeader from "./TicketSidebarHeader.vue";
import { ITicket } from "./symbols";

const ticket = inject(ITicket);
const data = computed(() => ticket.data);

const options = computed(() => [
  {
    field: "ticket_type",
    label: "Ticket type",
    store: useTicketTypeStore(),
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
    onError: useError(),
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
