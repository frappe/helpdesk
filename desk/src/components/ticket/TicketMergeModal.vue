<template>
  <Dialog
    :options="{ title: `Merge with another ticket` }"
    v-model="showDialog"
  >
    <template #body-content>
      <p class="text-p-base text-ink-gray-8 mb-4">
        This will merge all comments and emails of the ticket
        <span class="whitespace-nowrap font-semibold">#{{ ticket.name }}</span>
        with the selected ticket. This change is irreversible!
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
      >
      </Link>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Dialog } from "frappe-ui";
import { Ticket } from "@/types";

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

const targetTicket = ref("");

interface Filter {
  status: [string, string[] | string];
  is_merged: number;
  name: string[];
  customer?: any;
  contact?: string;
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
    return filters;
  }
  // otherwise show all tickets of the contact who created the ticket
  if (props.ticket.contact?.name) {
    filters["contact"] = props.ticket.contact.name;
  }
  return filters;
}
</script>

<style scoped></style>
