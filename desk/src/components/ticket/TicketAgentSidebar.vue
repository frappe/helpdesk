<template>
  <div class="flex w-[382px] flex-col justify-between border-l">
    <div
      class="flex h-10.5 items-center border-b px-5 py-2.5 text-lg font-medium text-ink-gray-9 justify-between"
    >
      <span
        class="cursor-copy text-lg font-semibold"
        @click="copyToClipboard(ticket.name, ticket.name)"
        >#{{ ticket.name }}
      </span>
      <Dropdown
        :options="[
          {
            label: 'Merge Ticket',
            onClick: () => handleTicketMerge(),
            icon: LucideMerge,
          },
        ]"
      >
        <Button icon="more-horizontal" class="text-gray-600" variant="ghost" />
      </Dropdown>
    </div>
    <TicketAgentContact
      :contact="ticket.contact"
      @email:open="(e) => emit('email:open', e)"
    />
    <!-- feedback component -->
    <TicketFeedback
      v-if="ticket.feedback_rating"
      class="py-3 !px-6 !gap-3 text-base text-gray-600"
      :ticket="ticket"
    />
    <!-- ticket details -->
    <TicketAgentDetails :ticket="ticket" />
    <!-- fields -->
    <TicketAgentFields :ticket="ticket" @update="update" />
  </div>
</template>

<script setup lang="ts">
import TicketAgentDetails from "./TicketAgentDetails.vue";
import TicketAgentContact from "./TicketAgentContact.vue";
import TicketAgentFields from "./TicketAgentFields.vue";
import LucideMerge from "~icons/lucide/merge";
import { copyToClipboard } from "@/utils";
import { globalStore } from "@/stores/globalStore";
import { createResource } from "frappe-ui";

const props = defineProps({
  ticket: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(["update", "email:open"]);

const { $dialog } = globalStore();

function update(val) {
  if (typeof val.value === "object") {
    val.value = val.value.target?.value || null;
  }
  emit("update", val);
}

const resource = createResource({
  url: "helpdesk.helpdesk.doctype.hd_ticket.api.merge_ticket",
  params: {
    source: props.ticket.name,
    target: 5461,
  },
  onSuccess: (data) => {
    console.log("Ticket merged successfully", data);
  },
});

function handleTicketMerge() {
  $dialog({
    title: "Merge Ticket",
    message: "Are you sure you want to merge this ticket?",
    actions: [
      {
        label: "Confirm",
        variant: "solid",
        onClick(close) {
          resource.fetch();
          // close();
        },
      },
    ],
  });
}
</script>
