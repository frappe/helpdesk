<template>
  <div class="flex justify-between">
    <div class="flex gap-2">
      <PresetFilters doctype="HD Ticket" />
      <Dropdown
        :options="byStatus"
        :button="{
          label: 'Status',
          iconRight: 'chevron-down',
          variant: 'outline',
          size: 'sm',
        }"
      />
      <Dropdown
        :options="byPriority"
        :button="{
          label: 'Priority',
          iconRight: 'chevron-down',
          variant: 'outline',
          size: 'sm',
        }"
      />
    </div>
    <div class="flex items-center gap-2">
      <CompositeFilters />
      <Dropdown :options="sortOptions">
        <template #default>
          <Button label="Sort" variant="outline" size="sm">
            <template #prefix>
              <IconSort class="h-3 w-3" />
            </template>
          </Button>
        </template>
      </Dropdown>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRouter } from "vue-router";
import { useRoute } from "vue-router";
import { createResource, Dropdown } from "frappe-ui";
import { useTicketPriorityStore } from "@/stores/ticketPriority";
import { useTicketStatusStore } from "@/stores/ticketStatus";
import { useListFilters } from "@/composables/listFilters";
import CompositeFilters from "./CompositeFilters.vue";
import PresetFilters from "./PresetFilters.vue";
import IconSort from "~icons/lucide/arrow-down-up";

const router = useRouter();
const route = useRoute();
const ticketPriorityStore = useTicketPriorityStore();
const ticketStatusStore = useTicketStatusStore();
const listFilters = useListFilters();

const sortOptionsRes = createResource({
  url: "helpdesk.extends.doc.sort_options",
  auto: true,
  params: {
    doctype: "HD Ticket",
  },
});

const sortOptions = computed(() => {
  return sortOptionsRes.data?.map((o) => ({
    label: o,
    onClick: () =>
      router.push({
        query: {
          ...route.query,
          sort: encodeURIComponent(o.replaceAll(" ", "-")),
        },
      }),
  }));
});

const byStatus = computed(() =>
  ticketStatusStore.options.map((status) => ({
    label: status,
    onClick: () => filterByField("status", status),
  }))
);

const byPriority = computed(() =>
  ticketPriorityStore.names.map((priority) => ({
    label: priority,
    onClick: () => filterByField("priority", priority),
  }))
);

function filterByField(fieldname: string, value: string) {
  const f = [
    {
      fieldname,
      filter_type: "is",
      value,
    },
  ];

  listFilters.applyQuery(f);
}
</script>
