<template>
  <div class="flex flex-col border-l">
    <TicketSidebarHeader title="Actions" />
    <div class="flex flex-wrap gap-2 overflow-auto p-5">
      <span v-if="!actions.data" class="text-base">Nothing to show</span>
      <Button
        v-for="a in actions.data"
        :key="a.name"
        :label="a.button_label"
        theme="gray"
        variant="subtle"
        @click="() => eic.call(ticket.data, a.action)"
      >
        <template v-if="a.button_icon" #prefix>
          <Icon :icon="a.button_icon" />
        </template>
        <template v-if="a.is_external_link" #suffix>
          <LucideExternalLink class="h-4 w-4" />
        </template>
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { inject } from "vue";
import { createListResource } from "frappe-ui";
import TicketSidebarHeader from "./TicketSidebarHeader.vue";
import { ITicket } from "./symbols";

const ticket = inject(ITicket);
const actions = createListResource({
  doctype: "HD Action",
  auto: true,
  cache: "Actions",
  filters: {
    is_enabled: true,
  },
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
