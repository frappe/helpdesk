<template>
  <div class="flex flex-col">
    <PageTitle title="Teams">
      <template #right>
        <Button
          label="New team"
          theme="gray"
          variant="solid"
          @click="showNewDialog = !showNewDialog"
        >
          <template #prefix>
            <IconPlus class="h-4 w-4" />
          </template>
        </Button>
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
    <Dialog
      v-model="showNewDialog"
      :options="{
        title: 'New team',
      }"
    >
      <template #body-content>
        <form class="space-y-2" @submit.prevent="newTeam.submit">
          <FormControl
            v-model="newTeamTitle"
            label="Title"
            placeholder="Product experts"
            type="text"
          />
          <Button
            :disabled="isEmpty(newTeamTitle)"
            class="w-full"
            label="Create"
            theme="gray"
            variant="solid"
          />
        </form>
      </template>
    </Dialog>
  </div>
</template>
<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { createResource, Dialog, FormControl } from "frappe-ui";
import { isEmpty } from "lodash";
import { AGENT_PORTAL_TEAM_SINGLE } from "@/router";
import { createToast } from "@/utils/toasts";
import { createListManager } from "@/composables/listManager";
import PageTitle from "@/components/PageTitle.vue";
import HelpdeskTable from "@/components/HelpdeskTable.vue";
import ListNavigation from "@/components/ListNavigation.vue";
import IconPlus from "~icons/lucide/plus";

const router = useRouter();
const showNewDialog = ref(false);
const newTeamTitle = ref(null);
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

const newTeam = createResource({
  url: "frappe.client.insert",
  makeParams() {
    return {
      doc: {
        doctype: "HD Team",
        team_name: newTeamTitle.value,
      },
    };
  },
  validate(params) {
    if (isEmpty(params.doc.team_name)) return "Title is required";
  },
  auto: false,
  onSuccess() {
    router.replace({
      name: AGENT_PORTAL_TEAM_SINGLE,
      params: {
        teamId: newTeamTitle.value,
      },
    });
  },
  onError(error) {
    const msg = error.message ? error.message : error.messages.join(", ");
    createToast({
      title: "Error creating team",
      text: msg,
      icon: "x",
      iconClasses: "text-red-500",
    });
  },
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
