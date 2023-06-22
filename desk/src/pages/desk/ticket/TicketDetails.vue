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
            @click="sidebar.isExpanded = false"
          />
        </div>
        <div class="my-6 flex flex-col justify-between gap-3.5">
          <div v-if="ticket.doc.customer" class="flex justify-between">
            <div class="text-gray-600">Customer:</div>
            <div class="font-medium text-gray-700">
              {{ ticket.doc.customer }}
            </div>
          </div>
          <div class="flex justify-between">
            <div class="text-gray-600">First Response Due:</div>
            <div class="font-medium text-gray-700">
              {{ firstResponseDue }}
            </div>
          </div>
          <div class="flex items-center justify-between">
            <div class="text-gray-600">Resolution Due:</div>
            <div class="font-medium text-gray-700">
              <span v-if="ticket.doc.resolution_by">
                {{ resolutionDue }}
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
          :value="changeAssignedTo || assignedTo"
          @change="changeAssignedTo = $event"
        />
      </div>
      <div class="flex flex-col gap-1">
        <div class="text-xs text-gray-600">Ticket Type</div>
        <Autocomplete
          v-model="ticket.doc.ticket_type"
          placeholder="Select a ticket type"
          :options="ticketTypeStore.dropdown"
          @update:modelValue="() => changedKeys.add('ticket_type')"
        />
      </div>
      <div class="flex gap-2">
        <div class="flex w-1/2 flex-col gap-1">
          <div class="text-xs text-gray-600">Priority</div>
          <Autocomplete
            v-model="ticket.doc.priority"
            placeholder="High"
            :options="ticketPriorityStore.dropdown"
            @update:modelValue="() => changedKeys.add('priority')"
          />
        </div>
        <div class="flex w-1/2 flex-col gap-1">
          <div class="text-xs text-gray-600">Status</div>
          <Autocomplete
            v-model="ticket.doc.status"
            placeholder="Open"
            :options="ticketStatusStore.dropdown"
            @update:modelValue="() => changedKeys.add('status')"
          />
        </div>
      </div>
      <div class="flex flex-col gap-1">
        <div class="text-xs text-gray-600">Team</div>
        <Autocomplete
          v-model="ticket.doc.agent_group"
          placeholder="Select a team"
          :options="teamStore.dropdown"
          @update:modelValue="() => changedKeys.add('agent_group')"
        />
      </div>
    </div>
    <div class="border-l">
      <div
        v-if="isSaveButtonVisible"
        class="mx-4 my-3.5 flex h-8 cursor-pointer items-center justify-center rounded-lg bg-gray-900 px-3 py-2 hover:bg-gray-800"
        @click="save"
      >
        <div class="text-base text-white">Save</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, Ref, watch } from "vue";
import { Autocomplete, Button } from "frappe-ui";
import dayjs from "dayjs";
import { useAgentStore } from "@/stores/agent";
import { useKeymapStore } from "@/stores/keymap";
import { useTeamStore } from "@/stores/team";
import { useTicketPriorityStore } from "@/stores/ticketPriority";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { useTicketTypeStore } from "@/stores/ticketType";
import { createToast } from "@/utils/toasts";
import { useTicketStore } from "./data";

const agentStore = useAgentStore();
const keymapStore = useKeymapStore();
const teamStore = useTeamStore();
const ticketPriorityStore = useTicketPriorityStore();
const ticketStatusStore = useTicketStatusStore();
const ticketTypeStore = useTicketTypeStore();
const { sidebar, ticket } = useTicketStore();

const isSaveButtonVisible = ref(false);

const firstResponseDue = computed(() =>
  dayjs(ticket.doc.response_by).format("MMMM D, h:mm A")
);
const resolutionDue = computed(() =>
  dayjs(ticket.doc.resolution_by).format("MMMM D, h:mm A")
);

/**
Fetch assignee info. This is expected to be a list of assigned users, even though we want
only one. This could be considered future proofing.
*/
ticket.getAssignees.fetch();

/**
Last assignee from the list, where expected list length is just one. Transformed into an
object to be used with `Autocomplete`
*/
const assignedTo = computed(() => {
  const assigned = (ticket.getAssignees.data?.message || []).pop();
  return agentStore.dropdown.find((agent) => agent.value === assigned?.name);
});

const changeAssignedTo: Ref = ref(null);

watch(
  changeAssignedTo,
  (changed) => (isSaveButtonVisible.value = changed.value)
);

/** 
This is used to keep track of changed keys. This is needed because updates are not
committed until save is called, unlike auto-update
*/
const changedKeys: Ref<Set<string>> = ref(new Set([]));

// Watch if any key is changed, and make save button visibility accordingly
watch(changedKeys, (keys) => (isSaveButtonVisible.value = !!keys.size), {
  deep: true,
});

// Add and remove shortcuts
const keyComboSave = ["Control", "S"];
onMounted(() => keymapStore.add(keyComboSave, save, "Save details"));
onUnmounted(() => keymapStore.remove(keyComboSave));

async function save() {
  const a = Array.from(changedKeys.value);

  /**
	Get an object with only changed keys and their values. The loop starts as an
	empty object, and adds keys and values into it
	*/
  const r = a.reduce((previous, current) => {
    previous[current] = ticket.doc[current].value;
    return previous;
  }, {});

  await ticket.setValue.submit(r);

  if (changeAssignedTo.value) {
    await ticket.assign.submit({
      agent: changeAssignedTo.value.value,
    });

    changeAssignedTo.value = null;
  }

  createToast({
    title: "Saved",
    icon: "check",
    iconClasses: "text-green-600",
  });

  changedKeys.value.clear();
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
