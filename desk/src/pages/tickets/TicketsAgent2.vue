<template>
  <div class="flex flex-col">
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
      :sort="{ sorts: sorts, sortableFields: sortableFields.data }"
      :column="{
        fields: fields,
        columns: columns,
      }"
      @event:sort="processSorts"
      @event:filter="processFilters"
      @event:column="processColumns"
    />
    <TicketsAgentList2
      :rows="items"
      :columns="columns"
      :page-length-count="pageLength"
      :options="{
        rowCount: rowCount,
        totalCount: totalCount,
      }"
      @update:page-length="updatePageLength"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useStorage } from "@vueuse/core";
import { createResource, Breadcrumbs } from "frappe-ui";
import TicketsAgentList2 from "./TicketsAgentList2.vue";
import { ViewControls, LayoutHeader } from "@/components";
import { useUserStore } from "@/stores/user";
const { getUser } = useUserStore();

const breadcrumbs = [{ label: "Tickets", route: { name: "TicketsAgent2" } }];
let storage = useStorage("tickets_agent", {
  filtersToApply: {},
  filters: [],
  sorts: [],
  sortsToApply: "modified desc",
  columns: [],
  rows: [],
});

let items = ref([]);
let columns = ref(storage.value.columns ? storage.value.columns : []);
let rows = ref(storage.value.rows ? storage.value.rows : []);
let fields = ref([]);
let rowCount = ref(0);
let totalCount = ref(0);

let filtersToApply = storage.value.filtersToApply;
let filters = ref(storage.value.filters);

let sorts = ref(storage.value.sorts);
let sortsToApply = storage.value.sortsToApply;

let pageLength = ref(20);

const tickets = createResource({
  url: "helpdesk.api.doc.get_list_data",
  params: {
    doctype: "HD Ticket",
    filters: filtersToApply,
    order_by: sortsToApply,
    page_length: pageLength.value,
    columns: columns.value.length ? columns.value : undefined,
    rows: rows.value.length ? rows.value : undefined,
  },
  auto: true,
  transform(data) {
    data.data.forEach((row) => {
      row.name = row.name.toString();
      let _user = getUser(JSON.parse(row._assign)[0]);

      row._assign = {
        name: _user.name,
        label: _user.full_name,
        image: _user.user_image,
      };
    });
  },
  onSuccess(data) {
    columns.value = data.columns;
    rows.value = data.rows;
    items.value = data.data;
    fields.value = data.fields;
    rowCount.value = data.row_count;
    totalCount.value = data.total_count;
  },
});

function updatePageLength(value) {
  if (value == "loadMore") {
    tickets.update({
      params: {
        doctype: "HD Ticket",
        filters: filtersToApply,
        order_by: sortsToApply,
        page_length: tickets.data.data.length + pageLength.value,
      },
    });
  } else {
    pageLength.value = value;
    tickets.update({
      params: {
        doctype: "HD Ticket",
        filters: filtersToApply,
        order_by: sortsToApply,
        page_length: pageLength.value,
      },
    });
  }

  tickets.reload();
}

function processColumns(columnEvent) {
  if (columnEvent.event === "add") {
    tickets.update({
      params: {
        order_by: sortsToApply,
        filters: filtersToApply,
        page_length: pageLength.value,
        columns: [columnEvent.data, ...columns.value],
        rows: [columnEvent.data.key, ...rows.value],
        doctype: "HD Ticket",
      },
    });
    storage.value.columns = [columnEvent.data, ...columns.value];
    storage.value.rows = [columnEvent.data.key, ...rows.value];
    tickets.reload();
  } else if (columnEvent.event === "remove") {
    tickets.update({
      params: {
        order_by: sortsToApply,
        filters: filtersToApply,
        page_length: pageLength.value,
        columns: columns.value.filter((column) => {
          return column.key != columnEvent.data.key;
        }),
        rows: rows.value.filter((row) => {
          return row != columnEvent.data.key;
        }),
        doctype: "HD Ticket",
      },
    });

    storage.value.columns = columns.value.filter((column) => {
      return column.key != columnEvent.data.key;
    });
    storage.value.rows = rows.value.filter((row) => {
      return row != columnEvent.data.key;
    });
    tickets.reload();
  } else if (columnEvent.event === "update") {
    storage.value.columns = columnEvent.data;
  }
}

function processSorts(sortEvent) {
  if (sortEvent.event === "add") {
    sorts.value.push(sortEvent.data);
    sortsToApply = sortEvent.data.sortToApply;
  } else if (sortEvent.event === "remove") {
    sorts.value.splice(sortEvent.index, 1);
    sortsToApply = sortEvent.data.sortToApply;
  } else if (sortEvent.event === "clear") {
    sorts.value = [];
    sortsToApply = "modified desc";
  } else if (sortEvent.event === "update") {
    sorts.value[sortEvent.data.index] = sortEvent.data;
    sortsToApply = sortEvent.data.sortToApply;
  }

  storage.value.sorts = sorts.value;
  storage.value.sortsToApply = sortsToApply;

  tickets.update({
    params: {
      order_by: sortsToApply,
      filters: filtersToApply,
      page_length: 100,
      doctype: "HD Ticket",
    },
  });

  apply();
}

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
  } else if (filterEvent.event === "preset") {
    filters.value = filterEvent.data.filters;

    for (let filter in filtersToApply) delete filtersToApply[filter];
    Object.assign(filtersToApply, filterEvent.data.filtersToApply);
  }

  storage.value.filters = filters.value;
  storage.value.filtersToApply = filtersToApply;

  apply();
}

function apply() {
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

const sortableFields = createResource({
  url: "helpdesk.api.doc.sort_options",
  auto: true,
  params: {
    doctype: "HD Ticket",
  },
});
</script>
