<template>
  <div class="flex flex-col border-l">
    <TicketSidebarHeader title="Actions & Tags" />
    <span class="space-y-4 p-5">
      <div class="space-y-2">
        <div class="text-base font-medium">Actions</div>
        <div class="flex flex-wrap gap-2 overflow-auto">
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
      <div class="space-y-2">
        <div class="text-base font-medium">Tags</div>
        <div class="flex flex-wrap gap-2 overflow-auto">
          <Button
            v-for="tag in ticket.data.tags"
            :key="tag.name"
            :label="tag"
            theme="gray"
            variant="outline"
          >
            <template #suffix>
              <LucideX class="h-4 w-4" @click="rmTag.submit({ tag })" />
            </template>
          </Button>
          <FormControl
            v-if="showInput"
            type="text"
            placeholder="Tag"
            autofocus
            @keydown.enter="addTag.submit({ tag: $event.target.value })"
            @keydown.esc="showInput = false"
          >
            <template #prefix>
              <LucideTag class="h-4 w-4" />
            </template>
          </FormControl>
          <Button
            v-else
            theme="gray"
            variant="outline"
            @click="() => (showInput = true)"
          >
            <template #icon>
              <LucidePlus class="h-4 w-4" />
            </template>
          </Button>
        </div>
      </div>
    </span>
  </div>
</template>

<script setup lang="ts">
import { inject, ref } from "vue";
import { createResource, createListResource } from "frappe-ui";
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
const showInput = ref(false);
const addTag = createResource({
  url: "frappe.desk.doctype.tag.tag.add_tag",
  debounce: 300,
  makeParams: (params) => ({
    tag: params.tag,
    dt: "HD Ticket",
    dn: ticket.data.name,
  }),
  onSuccess: () => {
    ticket.reload().then(() => (showInput.value = false));
  },
});
const rmTag = createResource({
  url: "frappe.desk.doctype.tag.tag.remove_tag",
  debounce: 300,
  makeParams: (params) => ({
    tag: params.tag,
    dt: "HD Ticket",
    dn: ticket.data.name,
  }),
  onSuccess: () => ticket.reload(),
});

/**
 * Wrapper function for eval. Can be used with `.call()`. Helps in
 * forcing context
 */
function eic(s: string) {
  return eval(s);
}
</script>
