<template>
  <div class="flex flex-col">
    <PageTitle title="Canned Responses">
      <template #right>
        <Button
          label="New canned response"
          theme="gray"
          variant="solid"
          @click="showNewDialog = true"
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
      :data="responses.list?.data || []"
      row-key="name"
      :emit-row-click="true"
      :hide-checkbox="true"
      :hide-column-selector="true"
      @row-click="gotoResponse"
    />
    <ListNavigation class="p-3" v-bind="responses" />
    <AddNewCannedResponsesDialog
      :show="showNewDialog"
      @close="showNewDialog = false"
    />
  </div>
</template>
<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { AGENT_PORTAL_CANNED_RESPONSE_SINGLE } from "@/router";
import { createListManager } from "@/composables/listManager";
import PageTitle from "@/components/PageTitle.vue";
import HelpdeskTable from "@/components/HelpdeskTable.vue";
import ListNavigation from "@/components/ListNavigation.vue";
import AddNewCannedResponsesDialog from "@/components/desk/global/AddNewCannedResponsesDialog.vue";
import IconPlus from "~icons/lucide/plus";

const router = useRouter();
const showNewDialog = ref(false);
const columns = [
  {
    title: "Name",
    colKey: "name",
    colClass: "w-1/3",
  },
  {
    title: "Owner",
    colKey: "owner",
    colClass: "w-1/3",
  },
];

const responses = createListManager({
  doctype: "HD Canned Response",
  fields: ["name", "title", "owner"],
  auto: true,
});

function gotoResponse(id: string) {
  router.push({
    name: AGENT_PORTAL_CANNED_RESPONSE_SINGLE,
    params: {
      id,
    },
  });
}
</script>
