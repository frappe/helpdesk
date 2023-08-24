<template>
  <div class="flex flex-col">
    <PageTitle title="Support Policies">
      <template #right>
        <RouterLink :to="{ name: AGENT_PORTAL_SLA_NEW }">
          <Button label="New policy" theme="gray" variant="solid">
            <template #prefix>
              <IconPlus class="h-4 w-4" />
            </template>
          </Button>
        </RouterLink>
      </template>
    </PageTitle>
    <ListView
      :columns="columns"
      :data="policies.list?.data || []"
      :empty-message="emptyMessage"
      class="mt-2.5 grow"
      row-key="name"
    >
      <template #enabled="{ data }">
        <Badge :theme="data.enabled ? 'green' : 'gray'" variant="subtle">
          {{ data.enabled ? "Enabled" : "Disabled" }}
        </Badge>
      </template>
      <template #default_sla="{ data }">
        <Badge v-if="data.default_sla" theme="blue" variant="subtle"
          >Default</Badge
        >
      </template>
    </ListView>
    <ListNavigation :resource="policies" />
  </div>
</template>
<script setup lang="ts">
import { usePageMeta, Badge } from "frappe-ui";
import { AGENT_PORTAL_SLA_NEW, AGENT_PORTAL_SLA_SINGLE } from "@/router";
import { createListManager } from "@/composables/listManager";
import PageTitle from "@/components/PageTitle.vue";
import { ListView } from "@/components";
import ListNavigation from "@/components/ListNavigation.vue";
import IconPlus from "~icons/lucide/plus";

const emptyMessage = "No Support Policies Found";
const columns = [
  {
    label: "Name",
    key: "name",
    width: "w-80",
  },
  {
    label: "Status",
    key: "enabled",
    width: "w-80",
  },
  {
    label: "",
    key: "default_sla",
    width: "w-80",
  },
];

const policies = createListManager({
  doctype: "HD Service Level Agreement",
  fields: ["name", "default_sla", "enabled"],
  auto: true,
  transform: (data) => {
    for (const d of data) {
      d.onClick = {
        name: AGENT_PORTAL_SLA_SINGLE,
        params: {
          id: d.name,
        },
      };
    }
    return data;
  },
});

usePageMeta(() => {
  return {
    title: "Support policies",
  };
});
</script>
