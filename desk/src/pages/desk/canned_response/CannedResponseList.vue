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
            <LucidePlus class="h-4 w-4" />
          </template>
        </Button>
      </template>
    </PageTitle>
    <ListView
      :columns="columns"
      :resource="responses"
      class="mt-2.5"
      doctype="HD Canned Response"
    />
    <AddNewCannedResponsesDialog
      :show="showNewDialog"
      @close="showNewDialog = false"
    />
  </div>
</template>
<script setup lang="ts">
import { ref } from "vue";
import { usePageMeta } from "frappe-ui";
import { AGENT_PORTAL_CANNED_RESPONSE_SINGLE } from "@/router";
import { createListManager } from "@/composables/listManager";
import PageTitle from "@/components/PageTitle.vue";
import { ListView } from "@/components";
import AddNewCannedResponsesDialog from "@/components/desk/global/AddNewCannedResponsesDialog.vue";

const showNewDialog = ref(false);
const emptyMessage = "No Canned Responses Found";
const columns = [
  {
    label: "Name",
    key: "name",
    width: "w-80",
  },
  {
    label: "Owner",
    key: "owner",
    width: "w-96",
  },
];

const responses = createListManager({
  doctype: "HD Canned Response",
  fields: ["name", "title", "owner"],
  auto: true,
  transform: (data) => {
    for (const d of data) {
      d.onClick = {
        name: AGENT_PORTAL_CANNED_RESPONSE_SINGLE,
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
    title: "Canned responses",
  };
});
</script>
