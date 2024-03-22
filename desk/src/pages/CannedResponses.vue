<template>
  <div class="flex flex-col">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="breadcrumbs" />
      </template>
      <template #right-header>
        <Button
          label="Create"
          theme="gray"
          variant="solid"
          @click="showNewDialog = true"
        >
          <template #prefix>
            <LucidePlus class="h-4 w-4" />
          </template>
        </Button>
      </template>
    </LayoutHeader>
    <ListView
      class="px-5 pt-2"
      :columns="cannedResponses?.data?.columns"
      :rows="cannedResponses?.data?.data"
      :options="{
        getRowRoute: (row) => ({
          name: 'CannedResponse',
          params: { id: row.name },
        }),
        selectable: true,
        showTooltip: false,
      }"
    />
    <AddNewCannedResponseDialog
      :show="showNewDialog"
      @close="showNewDialog = false"
    />
  </div>
</template>
<script setup lang="ts">
import { ref } from "vue";
import { createResource, Breadcrumbs, ListView } from "frappe-ui";
import { AddNewCannedResponseDialog } from "@/components/canned-response/";
import { LayoutHeader } from "@/components";

const breadcrumbs = [
  { label: "Canned Responses", route: { name: "CannedResponses" } },
];

const showNewDialog = ref(false);

const cannedResponses = createResource({
  url: "helpdesk.api.doc.get_list_data",
  params: {
    doctype: "HD Canned Response",
  },
  auto: true,
});
</script>
