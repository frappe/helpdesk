<template>
    <div class="flex-col">
      <LayoutHeader>
        <template #left-header>
          <Breadcrumbs :items="breadcrumbs" />
        </template>
        <template #right-header>
          <Button variant="solid" label="Create" @click="showNewDialog = true">
            <template #prefix>
              <FeatherIcon name="plus" class="h-4" />
            </template>
          </Button>
        </template>
      </LayoutHeader>
      <ViewControls :filter="{ filters: filters, filterableFields: filterableFields.data }"
        @event:filter="processFilters" />
      <TicketsAgentList2 class="px-5" :rows="rows" :columns="columns" />
    </div>
  </template>
  
  <script setup lang="ts">
  
  import { ref } from 'vue';
  import { createResource, Breadcrumbs } from 'frappe-ui';
  import TicketsAgentList2 from "./TicketsAgentList2.vue";
  import { ViewControls } from '@/components';
  
  const breadcrumbs = [{ label: 'Tickets', route: { name: 'TicketsAgent' } }];
  const showNewDialog = ref(false);
  let columns = ref([]);
  let rows = ref([]);
  
  let filtersToApply = {};
  let filters = ref([]);
  
  const tickets = createResource({
    url: 'helpdesk.api.doc.get_list_data',
    params: {
      doctype: 'HD Ticket',
      filters: filtersToApply,
      order_by: 'modified desc',
    },
    auto: true,
    onSuccess(data) {
      columns.value = data.columns;
      rows.value = data.data;
    }
  });
  
  function processFilters(filterEvent) {
  
    if (filterEvent.event === 'add') {
      const key = filterEvent.data.field.fieldname;
      const { filterToApply } = filterEvent.data;
  
      filters.value.push(filterEvent.data);
      filtersToApply[key] = filterToApply[key];
  
    } else if (filterEvent.event === 'remove') {
      const key = filters.value[filterEvent.index].field.fieldname;
      filters.value.splice(filterEvent.index, 1);
      delete filtersToApply[key];
  
    } else if (filterEvent.event === 'update') {
      const key = filterEvent.data.field.fieldname;
      const oldKey = filters.value[filterEvent.data.index].field.fieldname;
  
      const { filterToApply } = filterEvent.data;
  
      filters.value[filterEvent.data.index] = filterEvent.data;
      delete filtersToApply[oldKey];
  
      filtersToApply[key] = filterToApply[key];
  
    } else if (filterEvent.event === 'clear') {
      filters.value = [];
      for (let filter in filtersToApply) delete filtersToApply[filter];
    }
  
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
      return data.sort((fieldA, fieldB) => {
        const labelA = fieldA.label.toUpperCase();
        const labelB = fieldB.label.toUpperCase();
        if (labelA < labelB) {
          return -1;
        }
        if (labelA > labelB) {
          return 1;
        }
  
        return 0;
      }).map((field) => {
        return {
          label: field.label,
          value: field.fieldname,
          ...field,
        }
      })
    },
  });
  
  </script>