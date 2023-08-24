<template>
  <PageTitle class="border-b">
    <template #title>
      <BreadCrumbs
        :items="[
          {
            label: 'Tickets',
            route: {
              name: AGENT_PORTAL_TICKET_LIST,
            },
          },
          {
            label: data.subject,
          },
        ]"
      />
    </template>
    <template #right>
      <Autocomplete
        :options="agentStore.dropdown"
        :value="
          assignedTo
            ? {
                label: assignedTo?.full_name,
                value: assignedTo?.name,
              }
            : null
        "
        placeholder="Assign an agent"
        @change="assignAgent($event.value)"
      >
        <template #prefix>
          <Avatar
            v-if="assignedTo"
            class="mr-2"
            size="sm"
            :label="assignedTo?.full_name"
            :image="assignedTo?.user_image"
          />
        </template>
        <template #item-prefix="{ option }">
          <Avatar
            class="mr-2"
            :label="userStore.getUser(option.value)?.full_name"
            :image="userStore.getUser(option.value)?.user_image"
          />
        </template>
      </Autocomplete>
    </template>
  </PageTitle>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { createResource, Autocomplete, Avatar } from "frappe-ui";
import { AGENT_PORTAL_TICKET_LIST } from "@/router";
import { emitter } from "@/emitter";
import { createToast } from "@/utils";
import { useAgentStore } from "@/stores/agent";
import { useUserStore } from "@/stores/user";
import { useError } from "@/composables/error";
import { BreadCrumbs, PageTitle } from "@/components";
import { useTicket } from "./data";

const agentStore = useAgentStore();
const userStore = useUserStore();
const ticket = useTicket();
const data = computed(() => ticket.value.data);
const assignedTo = computed(() => {
  const assignJson = JSON.parse(data.value._assign);
  const arr = Array.isArray(assignJson) ? assignJson : [];
  const user = arr.slice(-1).pop();
  return userStore.getUser(user);
});

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
    onError: useError(),
  });
}
</script>
