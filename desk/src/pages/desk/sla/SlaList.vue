<template>
  <div class="flex flex-col">
    <PageTitle title="Support Policies">
      <template #right>
        <RouterLink :to="{ name: AGENT_PORTAL_SLA_NEW }">
          <Button
            icon-left="plus"
            label="New policy"
            class="bg-gray-900 text-white hover:bg-gray-800"
          />
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
        <Badge :color="data.enabled ? 'green' : ''">
          {{ data.enabled ? "Enabled" : "Disabled" }}
        </Badge>
      </template>
      <template #default_sla="{ data }">
        <Badge v-if="data.default_sla" color="blue"> Default </Badge>
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
