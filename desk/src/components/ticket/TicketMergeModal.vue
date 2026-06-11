<template>
  <Dialog
    :options="{ title: `Merge with another ticket` }"
    v-model="showDialog"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <p class="text-p-base text-ink-gray-8">
          {{
            __(
              "All comments and emails from both tickets will be merged into the selected ticket"
            )
          }}
          <span class="whitespace-nowrap font-semibold">
            #{{ ticket.name
            }}<Popover
              trigger="hover"
              :hoverDelay="0.25"
              :placement="isRtl ? 'left' : 'right'"
              class="!inline-flex align-middle ms-1 -mt-1"
            >
              <template #target>
                <FeatherIcon name="info" class="size-4 cursor-pointer" />
              </template>

              <template #body-main>
                <div
                  class="text-sm text-ink-gray-6 p-2.5 bg-surface-white rounded-md max-w-[30rem] whitespace-pre-wrap leading-5"
                >
                  <span class="text-p-base">
                    {{
                      __("Tickets must meet the following conditions:")
                    }}</span
                  >
                  <ul class="list-disc pl-4 mt-1 space-y-1">
                    <li
                      v-for="(condition, index) in mergeConditions"
                      :key="index"
                    >
                      {{ __(condition.text) }}
                      <code
                        v-if="condition.code"
                        class="bg-surface-gray-2 rounded-md px-1 py-0.5"
                      >
                        {{ __(condition.code) }}
                      </code>
                    </li>
                  </ul>
                </div>
              </template>
            </Popover>
          </span>
        </p>

        <Link
          class="form-control"
          doctype="HD Ticket"
          placeholder="Select Ticket"
          :filters="getDefaultFilters()"
          :label="__('Ticket')"
          :page-length="10"
          :value="targetTicket"
          :show-description="true"
          @change="targetTicket = String($event)"
        />
        <FormControl
          v-if="targetTicket"
          :label="__('Ticket Subject')"
          type="text"
          v-model="subject"
          :disabled="true"
        />
        <!-- banner -->
        <div
          class="flex items-center gap-2 rounded-md p-2 ring-1 ring-outline-gray-modals"
        >
          <TriangleAlert
            class="h-6 w-5 w-min-5 w-max-5 min-h-5 max-w-5 text-yellow-500"
          />

          <div class="text-wrap text-sm text-ink-gray-7">
            {{ __("This action is irreversible.") }}
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
import { Link } from "@/components";
import { __ } from "@/translation";
import { HDTicket } from "@/types/doctypes";
import {
  Dialog,
  createListResource,
  createResource,
  Popover,
  toast,
} from "frappe-ui";
import { ref, watch } from "vue";
import LucideMerge from "~icons/lucide/merge";
import TriangleAlert from "~icons/lucide/triangle-alert";
// interface P
interface Props {
  ticket: HDTicket;
}

interface E {
  (event: "update"): void;
  //   (event: "rowClick", row: any): void;
}

const props = defineProps<Props>();
const emit = defineEmits<E>();
const showDialog = defineModel<boolean>();

const isRtl = document.documentElement.dir === "rtl";

const mergeConditions = [
  {
    text: "Ticket must be Open or Paused.",
    code: "status_category in ['Open', 'Paused']",
  },
  {
    text: "Ticket must not already be merged.",
    code: "is_merged === 0",
  },
  {
    text: "Source and target tickets which are to be merged cannot be the same.",
  },
  {
    text: "If source ticket has a customer, target must belong to the same customer.",
    code: "customer === source.customer",
  },
  {
    text: "If source ticket has a raised_by, target must share the same raised_by.",
    code: "raised_by === source.raised_by",
  },
];

interface Filter {
  status_category: [string, string[] | string];
  is_merged: number;
  name: string[];
  customer?: any;
  raised_by?: [string, string[] | string];
}

function getDefaultFilters() {
  const filters: Filter = {
    status_category: ["in", ["Open", "Paused"]],
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
    if (!source) throw { message: __("Category is required") };
    if (!target) throw { message: __("Ticket to merged with is required") };
  },
  onSuccess: () => {
    toast.success(__("Ticket merged successfully."));
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
