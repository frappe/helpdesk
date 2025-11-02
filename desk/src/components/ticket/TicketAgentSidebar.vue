<template>
  <div class="flex !w-[382px] flex-col justify-between border-l">
    <div
      class="flex h-10.5 items-center border-b px-5 py-2.5 text-lg font-medium text-ink-gray-9 justify-between"
    >
      <span
        class="cursor-copy text-lg font-semibold"
        @click="
          copyToClipboard(ticket.name, `'${ticket.name}' copied to clipboard`)
        "
        >#{{ ticket.name }}
      </span>
      <Dropdown
        v-if="showMergeOption"
        placement="right"
        :options="[
          {
            label: 'Merge Ticket',
            onClick: () => (showMergeModal = true),
            icon: LucideMerge,
            condition: () => !ticket.is_merged,
          },
        ]"
      >
        <Button icon="more-horizontal" class="text-gray-600" variant="ghost" />
      </Dropdown>
    </div>
    <TicketAgentContact
      :contact="ticket.contact"
      :ticketId="ticket.name"
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
    <TicketMergeModal
      :ticket="ticket"
      v-if="showMergeModal"
      v-model="showMergeModal"
      @update="emit('reload')"
    />
  </div>
</template>

<script setup lang="ts">
import { Ticket } from "@/types";
import { copyToClipboard } from "@/utils";
import { computed, ref } from "vue";
import LucideMerge from "~icons/lucide/merge";
import TicketAgentContact from "./TicketAgentContact.vue";
import TicketAgentDetails from "./TicketAgentDetails.vue";
import TicketAgentFields from "./TicketAgentFields.vue";
import TicketMergeModal from "./TicketMergeModal.vue";

interface Props {
  ticket: Ticket;
}

const props = defineProps<Props>();

const emit = defineEmits(["update", "email:open", "reload"]);

function update(val = null) {
  if (val.value && typeof val.value === "object") {
    val.value = val.value.target?.value || null;
  }
  emit("update", val);
}

const showMergeModal = ref(false);

const showMergeOption = computed(() => {
  return (
    !props.ticket.is_merged &&
    ["Open", "Paused"].includes(props.ticket.status_category)
  );
});
</script>
