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
      v-slot="{ list }"
      :options="options"
      @emptyStateAction="isDialogVisible = true"
    />
    <AddNewAgentsDialog
      :show="isDialogVisible"
      @close="isDialogVisible = false"
    />
  </div>
</template>
<script setup lang="ts">
import { computed, ref, h } from "vue";
import { usePageMeta, Avatar } from "frappe-ui";
import AddNewAgentsDialog from "@/components/desk/global/AddNewAgentsDialog.vue";
import { LayoutHeader } from "@/components";

import ListViewBuilder from "../../../components/ListViewBuilder.vue";

const isDialogVisible = ref(false);

const options = computed(() => {
  return {
    doctype: "HD Agent",
    default_filters: { is_active: ["=", "1"] },
    column_config: {
      agent_name: {
        prefix: ({ row }) => {
          return h(Avatar, {
            shape: "circle",
            image: row.user_image,
            label: row.agent_name,
            size: "sm",
          });
        },
      },
    },
  };
});

usePageMeta(() => {
  return {
    title: "Agents",
  };
});
</script>
