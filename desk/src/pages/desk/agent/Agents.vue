<template>
  <div class="flex flex-col">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg font-medium text-gray-900">Agents</div>
      </template>
      <template #right-header>
        <Button
          label="New agent"
          theme="gray"
          variant="solid"
          @click="isDialogVisible = !isDialogVisible"
        >
          <template #prefix>
            <LucidePlus class="h-4 w-4" />
          </template>
        </Button>
      </template>
    </LayoutHeader>
    <div v-if="filterableFields.data">
      {{ filterableFields.data }}
    </div>
    <!-- <ViewControls
      :filter="{ filters: filters, filterableFields: filterableFields.data }"
      :sort="{ sorts: sorts, sortableFields: sortableFields.data }"
      :column="{
        fields: fields,
        columns: columns,
      }"
    /> -->
    <AddNewAgentsDialog
      :show="isDialogVisible"
      @close="isDialogVisible = false"
    />
  </div>
</template>
<script setup lang="ts">
import { ref } from "vue";
import { usePageMeta, Avatar, Badge } from "frappe-ui";
import AddNewAgentsDialog from "@/components/desk/global/AddNewAgentsDialog.vue";
import LayoutHeader from "@/components/LayoutHeader.vue";
import { createResource } from "frappe-ui";
// import ViewControls from "@/components/ViewControls.vue";

const isDialogVisible = ref(false);

const agents = createResource({
  url: "helpdesk.api.doc.get_list_data",
  params: {
    doctype: "HD Agent",
  },
  auto: true,
  onSuccess: (response) => {
    console.log(response);
  },
});
const filterableFields = createResource({
  url: "helpdesk.api.doc.get_filterable_fields",
  cache: ["DocField", "HD Agent"],
  auto: true,
  params: {
    doctype: "HD Agent",
    append_assign: true,
  },
  transform: (data) => {
    return data.map((field) => {
      return {
        label: field.label,
        value: field.fieldname,
        ...field,
      };
    });
  },
});

const sortableFields = createResource({
  url: "helpdesk.api.doc.sort_options",
  auto: true,
  params: {
    doctype: "HD Agent",
  },
  onSuccess: (response) => {
    console.log("SORT FIELDS", response);
  },
});

usePageMeta(() => {
  return {
    title: "Agents",
  };
});
</script>
