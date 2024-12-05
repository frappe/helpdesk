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

    <ListViewBuilder
      doctype="HD Agent"
      v-slot="{ list }"
      :default_filters="{ is_active: ['=', '1'] }"
    >
      <!-- <div v-if="!list.loading">
      </div> -->
      <!-- {{ list?.data?.columns }}
      <br />
      <br />
      <br />
      {{ list?.data?.data }} -->
    </ListViewBuilder>

    <AddNewAgentsDialog
      :show="isDialogVisible"
      @close="isDialogVisible = false"
    />
  </div>
</template>
<script setup lang="ts">
import { ref } from "vue";
import { usePageMeta } from "frappe-ui";
import AddNewAgentsDialog from "@/components/desk/global/AddNewAgentsDialog.vue";
import LayoutHeader from "@/components/LayoutHeader.vue";

import ListViewBuilder from "../../../components/ListViewBuilder.vue";

const isDialogVisible = ref(false);

usePageMeta(() => {
  return {
    title: "Agents",
  };
});
</script>
