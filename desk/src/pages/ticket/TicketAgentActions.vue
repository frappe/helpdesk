<template>
  <span class="flex gap-2">
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
    <Button
      v-for="a in actions.data?.slice(0, 1)"
      :key="a.name"
      :label="a.button_label"
      theme="gray"
      variant="solid"
      @click="() => eic.call(ticket.data, a.action)"
    >
      <template v-if="a.button_icon" #prefix>
        <Icon :icon="a.button_icon" />
      </template>
      <template v-if="a.is_external_link" #suffix>
        <Icon icon="lucide:external-link" />
      </template>
    </Button>
    <Dropdown
      :options="
        actions.data?.slice(1).map((o) => ({
          label: o.button_label,
          onClick: () => eic.call(ticket.data, o.action),
        }))
      "
    >
      <Button theme="gray" variant="ghost">
        <Icon icon="lucide:more-horizontal" />
      </Button>
    </Dropdown>
  </span>
</template>

<script setup lang="ts">
import { computed, inject } from "vue";
import {
  createResource,
  createListResource,
  Autocomplete,
  Avatar,
  Button,
  Dropdown,
} from "frappe-ui";
import { Icon } from "@iconify/vue";
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

const actions = createListResource({
  doctype: "HD Action",
  auto: true,
  cache: "Actions",
  fields: [
    "name",
    "button_label",
    "button_icon",
    "is_external_link",
    "action",
    "cond_hidden",
  ],
  transform: (data) => {
    const res = [];
    for (const row of data) {
      const isHidden = eic.call(ticket.data, row.cond_hidden);
      if (!isHidden) res.push(row);
    }
    return res;
  },
});

/**
 * Wrapper function for eval. Can be used with `.call()`. Helps in
 * forcing context
 */
function eic(s: string) {
  return eval(s);
}
</script>
