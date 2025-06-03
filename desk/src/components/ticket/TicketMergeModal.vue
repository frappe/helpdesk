<template>
  <Dialog
    :options="{ title: `Merge with another ticket` }"
    v-model="showDialog"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <p class="text-p-base text-ink-gray-8">
          All comments and emails of the ticket
          <span class="whitespace-nowrap font-semibold"
            >#{{ ticket.name }}</span
          >
          will be moved to the selected ticket.
        </p>
        <Link
          class="form-control"
          doctype="HD Ticket"
          placeholder="Select Ticket"
          :filters="getDefaultFilters()"
          label="Ticket"
          :page-length="10"
          :value="targetTicket"
          :show-description="true"
          @change="targetTicket = String($event)"
        />
        <FormControl
          v-if="targetTicket"
          label="Ticket Subject"
          type="text"
          v-model="subject"
          :disabled="true"
        />
        <!-- banner -->
        <div
          class="flex items-center gap-2 rounded-md p-2 ring-1 ring-gray-200"
        >
          <TriangleAlert
            class="h-6 w-5 w-min-5 w-max-5 min-h-5 max-w-5 text-yellow-500"
          />

          <div class="text-wrap text-sm text-gray-700">
            This action is irreversible.
          </div>
        </div>
      </div>
    </template>
    <template #actions>
      <Button
        class="w-full"
        variant="solid"
        :label="
          targetTicket ? `Merge with ticket #${targetTicket} ` : 'Select Ticket'
        "
        :loading="mergeTicket.loading"
        :icon-left="targetTicket && LucideMerge"
        @click="handleTicketMerge"
      />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { Ticket } from "@/types";
import { Dialog, createListResource, createResource, toast } from "frappe-ui";
import { ref, watch } from "vue";
import LucideMerge from "~icons/lucide/merge";
import TriangleAlert from "~icons/lucide/triangle-alert";
// interface P
interface Props {
  ticket: Ticket;
}

interface E {
  (event: "update"): void;
  //   (event: "rowClick", row: any): void;
}

const props = defineProps<Props>();
const emit = defineEmits<E>();
const showDialog = defineModel<boolean>();

interface Filter {
  status: [string, string[] | string];
  is_merged: number;
  name: string[];
  customer?: any;
  raised_by?: [string, string[] | string];
}

function getDefaultFilters() {
  const filters: Filter = {
    status: ["in", ["Open", "Replied"]],
    is_merged: 0,
    name: ["!=", props.ticket.name],
  };
  // if part of an organization show all tickets of the organization
  if (props.ticket.customer) {
    filters.customer = props.ticket.customer;
  }
  //  show all tickets of the person who raised the ticket
  if (props.ticket.raised_by) {
    filters.raised_by = ["like", `%${props.ticket.raised_by}%`];
  }
  return filters;
}

const targetTicket = ref(null);
const subject = ref(null);

const mergeTicket = createResource({
  url: "helpdesk.helpdesk.doctype.hd_ticket.api.merge_ticket",
  makeParams({ source, target }) {
    return {
      source,
      target,
    };
  },
  validate({ source, target }) {
    if (!source) throw { message: "Category is required" };
    if (!target) throw { message: "Ticket to merged with is required" };
  },
  onSuccess: () => {
    toast.success("Ticket merged successfully");
    emit("update");

    showDialog.value = false;
    // open the target Ticket
    window.open(
      window.location.origin + "/helpdesk/tickets/" + targetTicket.value,
      "_blank"
    );
    targetTicket.value = null;
  },
});

const getTicketSubject = createListResource({
  doctype: "HD Ticket",
  filters: {
    name: ["=", targetTicket],
  },
  fields: ["subject"],
  onSuccess: (data: any) => {
    if (data.length > 0) {
      subject.value = data[0].subject;
    }
  },
});

watch(
  () => targetTicket.value,
  (newValue) => {
    if (newValue) {
      getTicketSubject.update({
        filters: {
          name: ["=", newValue],
        },
      });
      getTicketSubject.reload();
    }
  }
);

function handleTicketMerge() {
  mergeTicket.submit({
    source: props.ticket.name,
    target: targetTicket.value,
  });
}
</script>

<style scoped></style>
