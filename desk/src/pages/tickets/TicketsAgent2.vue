<template>
  <div class="flex-col">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="breadcrumbs" />
      </template>
      <template #right-header>
        <RouterLink :to="{ name: 'TicketAgentNew2' }">
          <Button label="Create" theme="gray" variant="solid">
            <template #prefix>
              <LucidePlus class="h-4 w-4" />
            </template>
          </Button>
        </RouterLink>
      </template>
    </LayoutHeader>
    <ViewControls
      :filter="{ filters: filters, filterableFields: filterableFields.data }"
      @event:filter="processFilters"
    />
    <TicketsAgentList2 class="px-5" :rows="rows" :columns="columns" />
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useStorage } from '@vueuse/core';
import { createResource, Breadcrumbs } from "frappe-ui";
import TicketsAgentList2 from "./TicketsAgentList2.vue";
import { ViewControls, LayoutHeader } from "@/components";

const breadcrumbs = [{ label: "Tickets", route: { name: "TicketsAgent2" } }];
let storage = useStorage("filter_ticket_agent", {
  filtersToApply: {},
  filters: [],
});
let columns = ref([]);
let rows = ref([]);

let filtersToApply = storage.value.filtersToApply;
let filters = ref(storage.value.filters);

const tickets = createResource({
  url: "helpdesk.api.doc.get_list_data",
  params: {
    doctype: "HD Ticket",
    filters: filtersToApply,
    order_by: "modified desc",
    page_length: 100,
  },
  auto: true,
  onSuccess(data) {
    columns.value = data.columns;
    rows.value = data.data;
  },
});

function processFilters(filterEvent) {
  if (filterEvent.event === "add") {
    const key = filterEvent.data.field.fieldname;
    const { filterToApply } = filterEvent.data;

    filters.value.push(filterEvent.data);
    filtersToApply[key] = filterToApply[key];
  } else if (filterEvent.event === "remove") {
    const key = filters.value[filterEvent.index].field.fieldname;
    filters.value.splice(filterEvent.index, 1);
    delete filtersToApply[key];
  } else if (filterEvent.event === "update") {
    const key = filterEvent.data.field.fieldname;
    const oldKey = filters.value[filterEvent.data.index].field.fieldname;

    const { filterToApply } = filterEvent.data;

    filters.value[filterEvent.data.index] = filterEvent.data;
    delete filtersToApply[oldKey];

    filtersToApply[key] = filterToApply[key];
  } else if (filterEvent.event === "clear") {
    filters.value = [];
    for (let filter in filtersToApply) delete filtersToApply[filter];
  }

  storage.value.filters = filters.value;
  storage.value.filtersToApply = filtersToApply;
  applyFilters();
}

function applyFilters() {
  tickets.reload();
}

const filterableFields = createResource({
  url: "helpdesk.api.doc.get_filterable_fields",
  cache: ["DocField", "HD Ticket"],
  auto: true,
  params: {
    doctype: "HD Ticket",
    append_assign: true,
  },
  transform: (data) => {
    return data
      .sort((fieldA, fieldB) => {
        const labelA = fieldA.label.toUpperCase();
        const labelB = fieldB.label.toUpperCase();
        if (labelA < labelB) {
          return -1;
        }
        if (labelA > labelB) {
          return 1;
        }

        return 0;
      })
      .map((field) => {
        return {
          label: field.label,
          value: field.fieldname,
          ...field,
        };
      });
  },
});
</script>
