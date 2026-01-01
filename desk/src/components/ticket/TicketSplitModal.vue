<template>
  <Dialog :options="{ title: __('Split ticket') }" v-model="showDialog">
    <template #body-content>
      <div class="flex flex-col gap-4">
        <p class="text-p-base text-ink-gray-8">
          {{ __("All") }}
          <span class="underline">{{ __("emails/ comments") }}</span>
          {{ __("from this email onwards will be moved to new ticket.") }}
        </p>
        <FormControl
          :label="__('New Ticket Subject')"
          type="text"
          v-model="subject"
          :placeholder="__('Add a subject for the new ticket')"
        />
        <div
          class="flex items-center gap-2 rounded-md p-2 ring-1 ring-gray-200"
        >
          <TriangleAlert
            class="h-6 w-5 w-min-5 w-max-5 min-h-5 max-w-5 text-yellow-500"
          />

          <div class="text-wrap text-sm text-gray-700">
            {{ __("This action is irreversible.") }}
          </div>
        </div>
      </div>
    </template>
    <template #actions>
      <Button
        class="w-full"
        variant="solid"
        :label="__('Split into new ticket')"
        :loading="splitTicket.loading"
        :icon-left="LucideSplit"
        @click="handleTicketSplit"
      />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { Dialog, createResource, toast } from "frappe-ui";
import { ref } from "vue";
import LucideSplit from "~icons/lucide/split";
import TriangleAlert from "~icons/lucide/triangle-alert";
import { __ } from "@/translation";

interface Props {
  ticket_id: string;
  communication_id: string;
}

interface E {
  (event: "update"): void;
  //   (event: "rowClick", row: any): void;
}

const props = defineProps<Props>();
const emit = defineEmits<E>();
const showDialog = defineModel<boolean>();

const subject = ref(null);

const splitTicket = createResource({
  url: "helpdesk.helpdesk.doctype.hd_ticket.api.split_ticket",
  makeParams({ subject, communication_id }) {
    return {
      subject,
      communication_id,
    };
  },
  validate({ subject, communication_id }) {
    if (!subject) throw { message: __("Subject is required") };
    if (!communication_id)
      throw { message: __("Communication ID is required") };
  },
  onSuccess: (newTicket: string) => {
    toast.success(__("Ticket split successfully"));
    showDialog.value = false;
    window.open(
      window.location.origin + "/helpdesk/tickets/" + newTicket,
      "_blank"
    );
    window.location.reload();
  },
});

function handleTicketSplit() {
  splitTicket.submit({
    subject: subject.value,
    communication_id: props.communication_id,
  });
}
</script>

<style scoped></style>
