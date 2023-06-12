<template>
  <div class="flex flex-col">
    <PageTitle title="Teams">
      <template #right>
        <RouterLink :to="{ name: AGENT_PORTAL_TEAM_NEW }">
          <Button
            label="New team"
            icon-left="plus"
            theme="gray"
            variant="solid"
          />
        </RouterLink>
      </template>
    </PageTitle>
    <HelpdeskTable
      class="grow"
      :columns="columns"
      :data="teams.list?.data || []"
      row-key="name"
      :emit-row-click="true"
      :hide-checkbox="true"
      :hide-column-selector="true"
      @row-click="gotoTeam"
    />
    <ListNavigation class="p-3" v-bind="teams" />
  </div>
</template>
<script setup lang="ts">
import { useRouter } from "vue-router";
import { AGENT_PORTAL_TEAM_NEW, AGENT_PORTAL_TEAM_SINGLE } from "@/router";
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
    title: "Assignment rule",
    colKey: "assignment_rule",
    colClass: "w-1/3",
  },
];

const teams = createListManager({
  doctype: "HD Team",
  fields: ["name", "assignment_rule"],
  auto: true,
});

function gotoTeam(id: string) {
  router.push({
    name: AGENT_PORTAL_TEAM_SINGLE,
    params: {
      teamId: id,
    },
  });
}
</script>
