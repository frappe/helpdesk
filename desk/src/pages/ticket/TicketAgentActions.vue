<template>
  <span>
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
  </span>
</template>

<script setup lang="ts">
import { computed, inject } from "vue";
import { createResource, Autocomplete, Avatar } from "frappe-ui";
import { emitter } from "@/emitter";
import { createToast } from "@/utils";
import { useAgentStore } from "@/stores/agent";
import { useUserStore } from "@/stores/user";
import { useError } from "@/composables/error";
import { ITicket } from "./symbols";

const ticket = inject(ITicket);
const agentStore = useAgentStore();
const userStore = useUserStore();
const data = computed(() => ticket.data);
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
