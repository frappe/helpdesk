<template>
  <div class="flex flex-col border-l">
    <TicketSidebarHeader title="Tags" />
    <div class="flex flex-wrap gap-2 overflow-auto p-5">
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
</template>

<script setup lang="ts">
import { inject, ref } from "vue";
import { createResource } from "frappe-ui";
import TicketSidebarHeader from "./TicketSidebarHeader.vue";
import { ITicket } from "./symbols";

const showInput = ref(false);
const ticket = inject(ITicket);
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
</script>
