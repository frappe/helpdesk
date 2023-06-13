<template>
  <Popover transition="default" :hide-on-blur="false">
    <template #target="{ togglePopover }">
      <Button
        label="Filters"
        variant="outline"
        size="sm"
        @click="togglePopover"
      >
        <template #prefix>
          <IconFilter class="h-3 w-3" />
        </template>
      </Button>
    </template>
    <template #body-main>
      <div class="flex flex-col gap-2 p-2">
        <div class="flex flex-col gap-2">
          <div v-for="(f, i) in filters" :key="i" class="flex gap-2 truncate">
            <div class="w-32">
              <Autocomplete
                v-model="f.field"
                :options="fields"
                placeholder="Field"
              />
            </div>
            <div class="w-24">
              <Autocomplete
                v-model="f.operator"
                :options="operators"
                placeholder="Type"
              />
            </div>
            <div class="w-32">
              <Autocomplete
                v-if="
                  f.field?.autocomplete__ &&
                  ['=', '!='].includes(f.operator?.value)
                "
                v-model="f.value"
                :options="f.field?.autocomplete__"
                placeholder="Value"
              />
              <Input v-else v-model="f.value" placeholder="Value" />
            </div>
            <Button
              icon="x"
              appearance="minimal"
              @click="() => removeFilter(i)"
            />
          </div>
        </div>
        <div class="flex justify-start gap-2">
          <Button label="Add a filter" @click="addFilter">
            <template #prefix>
              <IconPlus class="h-4 w-4" />
            </template>
          </Button>
          <Button
            v-if="!isEmpty(filters)"
            icon="check"
            appearance="primary"
            @click="applyFilters"
          />
          <Button
            v-if="!isEmpty(filters)"
            icon="x"
            appearance="danger"
            @click="clearFilters"
          />
        </div>
      </div>
    </template>
  </Popover>
</template>

<script setup lang="ts">
import { isEmpty } from "lodash";
import { Ref, ref, onMounted } from "vue";
import { Autocomplete, Popover } from "frappe-ui";
import { useListFilters } from "@/composables/listFilters";
import { useAgentStore } from "@/stores/agent";
import { useTicketPriorityStore } from "@/stores/ticketPriority";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { useTicketTypeStore } from "@/stores/ticketType";
import IconFilter from "~icons/lucide/list-filter";
import IconPlus from "~icons/lucide/plus";

type CompletionItem = {
  label: string;
  value: string;
};

type FilterItem = CompletionItem & {
  autocomplete__?: Array<CompletionItem>;
};

type FilterEntry = {
  field?: FilterItem;
  operator?: CompletionItem;
  value?: CompletionItem | string;
};

const agentStore = useAgentStore();
const ticketPriorityStore = useTicketPriorityStore();
const ticketStatusStore = useTicketStatusStore();
const ticketTypeStore = useTicketTypeStore();
const filters: Ref<Array<FilterEntry>> = ref([{}]);
const listFilters = useListFilters();

const fields: Array<FilterItem> = [
  {
    label: "Subject",
    value: "subject",
  },
  {
    label: "Status",
    value: "status",
    autocomplete__: ticketStatusStore.options.map((s) => ({
      label: s,
      value: s,
    })),
  },
  {
    label: "Priority",
    value: "priority",
    autocomplete__: ticketPriorityStore.names.map((p) => ({
      label: p,
      value: p,
    })),
  },
  {
    label: "Type",
    value: "ticket_type",
    autocomplete__: ticketTypeStore.options.map((p) => ({
      label: p.name,
      value: p.name,
    })),
  },
  {
    label: "Assigned to",
    value: "_assign",
    autocomplete__: agentStore.options.map((a) => ({
      label: a.agent_name,
      value: a.name,
    })),
  },
];

const operators = [
  {
    label: "Is",
    value: "=",
  },
  {
    label: "Is not",
    value: "!=",
  },
  {
    label: "Like",
    value: "like",
  },
  {
    label: "Not like",
    value: "not like",
  },
];

function addFilter() {
  filters.value.push({});
}

function removeFilter(index: number) {
  filters.value.splice(index, 1);
  if (isEmpty(filters.value)) clearFilters();
}

function clearFilters() {
  filters.value = [{}];
  listFilters.applyQuery("");
}

function applyFilters() {
  const f = filters.value
    .filter((f) => f.field && f.operator && f.value)
    .map((f) => ({
      fieldname: f.field.value,
      filter_type: f.operator.value,
      value: typeof f.value === "string" ? f.value : f.value.value,
    }));

  listFilters.applyQuery(f);
}

onMounted(() => {
  const fromQuery = listFilters.fromQuery();

  if (isEmpty(fromQuery)) return;

  filters.value = fromQuery.map((i) => ({
    field: fields.find((f) => f.value === i.fieldname),
    operator: operators.find(
      (o) => o.label.toLowerCase() === i.filter_type.toLowerCase()
    ),
    value: i.value,
  }));
});
</script>
