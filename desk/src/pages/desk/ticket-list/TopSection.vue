<template>
  <div class="space-y-2">
    <div class="flex justify-between">
      <div class="flex flex-wrap items-center gap-2">
        <Dropdown :options="sortOptions">
          <template #default>
            <Button label="Sort" variant="outline" size="sm">
              <template #prefix>
                <IconSort class="h-3 w-3" />
              </template>
            </Button>
          </template>
        </Dropdown>
        <FieldFilter doctype="HD Ticket" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRouter } from "vue-router";
import { useRoute } from "vue-router";
import { createResource, Dropdown } from "frappe-ui";
import FieldFilter from "@/components/FieldFilter.vue";
import IconSort from "~icons/lucide/arrow-down-up";

const router = useRouter();
const route = useRoute();

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
</script>
