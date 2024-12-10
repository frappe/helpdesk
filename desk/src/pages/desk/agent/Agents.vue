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
      :options="options"
      @empty-state-action="isDialogVisible = true"
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
import { LayoutHeader, ListViewBuilder } from "@/components";

const isDialogVisible = ref(false);

// filter not on first field/ datetime
// options mei route or click ka option
const options = computed(() => {
  return {
    doctype: "HD Agent",
    defaultFilters: { is_active: ["=", 1] },
    columnConfig: {
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
    emptyState: {
      title: "No Agents Found",
    },
  };
});

usePageMeta(() => {
  return {
    title: "Agents",
  };
});
</script>
