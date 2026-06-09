<template>
  <div class="flex flex-col">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg font-medium text-ink-gray-9">Tasks</div>
      </template>
      <template #right-header>
        <Button
          label="Create"
          theme="gray"
          variant="solid"
          @click="showNewTaskModal = !showNewTaskModal"
        >
          <template #prefix>
            <LucidePlus class="h-4 w-4" />
          </template>
        </Button>
      </template>
    </LayoutHeader>

    <ListViewBuilder
      ref="listViewRef"
      :options="options"
      @row-click="openTask"
      @empty-state-action="showNewTaskModal = true"
    />

    <NewTaskDialog
      v-model="showNewTaskModal"
      @task-created="handleTaskCreated"
    />

    <TaskboxEditor
      v-if="isTaskDialogVisible"
      v-model="isTaskDialogVisible"
      :task="selectedTask"
      :ticketId="selectedTask?.reference_docname || selectedTask?.ticket || ''"
      @submit="handleTaskUpdated"
    />
  </div>
</template>

<script setup lang="ts">
import { LayoutHeader, ListViewBuilder } from "@/components";
import NewTaskDialog from "@/components/desk/global/NewTaskDialog.vue";
import { toast, usePageMeta, call, Avatar } from "frappe-ui";
import { computed, h, ref } from "vue";
import TaskboxEditor    from "@/components/TaskboxEditor.vue";
import { showNewTaskModal } from "./dialogState";
import TaskIcon         from "@/components/icons/TaskIcon.vue";
import TaskStatusIcon   from "@/components/icons/TaskStatusIcon.vue";
import CalendarIcon     from "@/components/icons/CalendarIcon.vue";
import { dateFormat } from "@/utils";
import { __ } from "@/translation";
import { useUserStore } from "@/stores/user";

const { agentOptions } = useUserStore();

const isTaskDialogVisible = ref(false);
const selectedTask        = ref<any>(null);
const listViewRef         = ref<any>(null);

// ─── Refresh list in-place (no remount) ───────────────────────────────────────
function refreshList() {
  const lv = listViewRef.value;
  if (lv?.list?.reload) { lv.list.reload(); return; }
  if (lv?.list?.fetch)  { lv.list.fetch();  return; }
  if (lv?.reload)       { lv.reload();      return; }
  if (lv?.fetch)        { lv.fetch();       return; }
}

const hasActiveFilters = computed(
  () => Object.keys(listViewRef.value?.list?.params?.filters || {}).length > 0
);

const options = computed(() => ({
  doctype:          "HD Task",
  selectable:       true,
  showSelectBanner: true,
  columnConfig: {
    title: {},

    // Status — Second Column
    status: {
      custom: ({ item }: { item: any }) =>
        h(TaskStatusIcon, { status: item || "Backlog", class: "h-4 w-4" }),
    },

    // Priority — Third Column (FIXED: Standardized text string rendering block)
    priority: {
      custom: ({ item }: { item: any }) => {
        const priorityValue = typeof item === 'object' ? (item?.priority || item?.value) : item;
        return h(
          "span",
          { class: "text-sm text-ink-gray-7 font-medium" },
          priorityValue ? __(String(priorityValue)) : "-"
        );
      },
    },

    // Due Date — Fourth Column
    due_date: {
      custom: ({ item }: { item: any }) => {
        if (!item) return h("span", { class: "text-ink-gray-4" }, "-");
        return h("div", { class: "flex items-center gap-2 truncate text-base" }, [
          h(CalendarIcon, { class: "h-4 w-4 text-ink-gray-6" }),
          h("span", { class: "truncate" }, dateFormat(item, "D MMM, hh:mm a")),
        ]);
      },
    },

    // Assigned To — Fifth Column
    assigned: {
      custom: ({ item }: { item: any }) => {
        const email = typeof item === "string"
          ? item
          : (item?.assigned || item?.assigned_to || item?.email || item?.name || item?.full_name || "");

        if (!email) return h("span", { class: "text-ink-gray-4" }, "-");

        const agent = agentOptions.find((a) => a.value === email);
        return h("div", { class: "flex items-center gap-2 min-w-0" }, [
          h(Avatar, {
            shape: "circle",
            image: agent?.image ?? null,
            label: agent?.label ?? email,
            size:  "sm",
            class: "shrink-0",
          }),
          h("span", { class: "truncate text-ink-gray-8 font-medium" }, agent?.label ?? email),
        ]);
      },
    },
  },

  emptyState: {
    title: "No tasks found",
    icon:  h(TaskIcon, { class: "h-10 w-10 text-ink-gray-4" }),
    description: hasActiveFilters.value
      ? __("No tasks found for the applied filters. Try adjusting or clearing your filters.")
      : "",
  },
}));

// ─── Handlers ────────────────────────────────────────────────────────────────
function handleTaskCreated(): void {
  showNewTaskModal.value = false;
  refreshList();
}

async function openTask(id: string): Promise<void> {
  try {
    const task = await call("frappe.client.get", {
      doctype: "HD Task",
      name:    id,
    });
    selectedTask.value = {
      ...task,
      assigned: task.assigned || task.assigned_to || "",
    };
    isTaskDialogVisible.value = true;
  } catch {
    toast.error(__("Unable to load task details."));
  }
}

function handleTaskUpdated(): void {
  isTaskDialogVisible.value = false;
  selectedTask.value        = null;
  refreshList();
}

usePageMeta(() => ({ title: "Tasks" }));
</script>
