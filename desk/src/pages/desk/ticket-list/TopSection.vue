<template>
  <div class="space-y-2">
    <div class="flex justify-between">
      <FieldFilter doctype="HD Ticket" :append-assign="true" />
      <span class="flex items-center gap-2">
        <ColumnSelector id="ticket" :columns="columns" />
        <Dropdown :options="sortOptions">
          <template #default>
            <Button :label="getOrder() || 'Sort'" variant="outline" size="sm">
              <template #prefix>
                <Icon icon="lucide:arrow-down-up" />
              </template>
            </Button>
          </template>
        </Dropdown>
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { createResource, Button, Dropdown } from "frappe-ui";
import { Icon } from "@iconify/vue";
import { useOrder } from "@/composables/order";
import { ColumnSelector } from "@/components";
import FieldFilter from "@/components/FieldFilter.vue";

interface P {
  columns: any[];
}

defineProps<P>();

const { get: getOrder, set: setOrder } = useOrder();
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
    onClick: () => setOrder(o),
  }));
});
</script>
