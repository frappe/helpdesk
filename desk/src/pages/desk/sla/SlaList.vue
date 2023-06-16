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
    <HelpdeskTable
      class="grow"
      :columns="columns"
      :data="policies.list?.data || []"
      row-key="name"
      :emit-row-click="true"
      :hide-checkbox="true"
      :hide-column-selector="true"
      @row-click="gotoPolicy"
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
    </HelpdeskTable>
    <ListNavigation class="p-3" v-bind="policies" />
  </div>
</template>
<script setup lang="ts">
import { useRouter } from "vue-router";
import { Badge } from "frappe-ui";
import { AGENT_PORTAL_SLA_NEW, AGENT_PORTAL_SLA_SINGLE } from "@/router";
import { createListManager } from "@/composables/listManager";
import PageTitle from "@/components/PageTitle.vue";
import HelpdeskTable from "@/components/HelpdeskTable.vue";
import ListNavigation from "@/components/ListNavigation.vue";
import IconPlus from "~icons/lucide/plus";

const router = useRouter();
const columns = [
  {
    title: "Name",
    colKey: "name",
    colClass: "w-1/3",
  },
  {
    title: "Status",
    colKey: "enabled",
    colClass: "w-1/3",
  },
  {
    title: "",
    colKey: "default_sla",
    colClass: "w-1/3",
  },
];

const policies = createListManager({
  doctype: "HD Service Level Agreement",
  fields: ["name", "default_sla", "enabled"],
  auto: true,
});

function gotoPolicy(id: string) {
  router.push({
    name: AGENT_PORTAL_SLA_SINGLE,
    params: {
      id,
    },
  });
}
</script>
