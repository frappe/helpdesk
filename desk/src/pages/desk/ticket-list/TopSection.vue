<template>
  <div class="space-y-2">
    <div class="flex justify-between">
      <div class="flex flex-wrap items-center gap-2">
        <Dropdown :options="sortOptions">
          <template #default>
            <Button :label="getOrder() || 'Sort'" variant="outline" size="sm">
              <template #prefix>
                <IconSort class="h-3 w-3" />
              </template>
            </Button>
          </template>
        </Dropdown>
        <FieldFilter doctype="HD Ticket" :append-assign="true" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { createResource, Dropdown } from "frappe-ui";
import { useOrder } from "@/composables/order";
import FieldFilter from "@/components/FieldFilter.vue";
import IconSort from "~icons/lucide/arrow-down-up";

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
