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
      :key="reloadKey"
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
import { toast, usePageMeta, call, Avatar, createResource } from "frappe-ui";
import { computed, h, ref } from "vue";
import TaskboxEditor from "@/components/TaskboxEditor.vue";
import { showNewTaskModal } from "./dialogState";
import TaskIcon from "@/components/icons/TaskIcon.vue";
import TaskStatusIcon from "@/components/icons/TaskStatusIcon.vue";
import TaskPriorityIcon from "@/components/icons/TaskPriorityIcon.vue";
import CalendarIcon from "@/components/icons/CalendarIcon.vue";
import { formatDate } from "@/utils";
import { __ } from "@/translation";

const isTaskDialogVisible = ref(false);
const selectedTask        = ref<any>(null);
const listViewRef         = ref<any>(null);

// Incrementing this remounts ListViewBuilder completely, forcing a fresh fetch.
const reloadKey = ref(0);
function forceReload() {
  reloadKey.value++;
}

const agentsList = createResource({
  url: "frappe.client.get_list",
  params: {
    doctype:     "User",
    fields:      ["name", "full_name", "user_image"],
    filters:     { enabled: 1, user_type: "System User" },
    page_length: 200,
  },
  auto: true,
});

const agentOptions = computed(() => {
  if (!agentsList.data) return [];
  return (agentsList.data as any[]).map((u: any) => ({
    label: u.full_name || u.name,
    value: u.name,
    image: u.user_image || "",
  }));
});

const hasActiveFilters = computed(
  () => Object.keys(listViewRef.value?.list?.params?.filters || {}).length > 0
);

const options = computed(() => {
  return {
    doctype:          "HD Task",
    selectable:       true,
    showSelectBanner: true,
    columnConfig: {
      title: {},
      priority: {
        custom: ({ item }: { item: any }) => {
          return h(TaskPriorityIcon, { priority: item });
        },
      },
      assigned: {
        custom: ({ item }: { item: any }) => {
          // FIX: Return a placeholder instead of null so the cell remains clickable
          if (!item) return h("span", { class: "text-ink-gray-4" }, "-");
          
          const email = typeof item === "string"
            ? item
            : (item.assigned || item.assigned_to || item.email || item.name || item.full_name);
            
          if (!email) return h("span", { class: "text-ink-gray-4" }, "-");

          const agent = agentOptions.value.find((a) => a.value === email);
          return h("div", { class: "flex items-center gap-2 min-w-0" }, [
            h(Avatar, {
              shape: "circle",
              image: agent ? agent.image : null,
              label: agent ? agent.label : email,
              size:  "sm",
              class: "shrink-0",
            }),
            h("span", { class: "truncate text-ink-gray-8 font-medium" }, agent ? agent.label : email),
          ]);
        },
      },
      status: {
        custom: ({ item }: { item: any }) => {
          return h(TaskStatusIcon, { status: item, class: "h-4 w-4" });
        },
      },
      due_date: {
        custom: ({ item }: { item: any }) => {
          // FIX: Return a placeholder instead of null so the cell remains clickable
          if (!item) return h("span", { class: "text-ink-gray-4" }, "-");
          
          return h(
            "div",
            { class: "flex items-center gap-2 truncate text-base" },
            [
              h(CalendarIcon, { class: "h-4 w-4 text-ink-gray-6" }),
              h("span", { class: "truncate" }, formatDate(item, "D MMM, hh:mm a")),
            ],
          );
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
  };
});
function handleTaskCreated(): void {
  showNewTaskModal.value = false;
  forceReload();
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
  } catch (error) {
    toast.error(__("Unable to load task details."));
  }
}

function handleTaskUpdated(): void {
  isTaskDialogVisible.value = false;
  selectedTask.value        = null;
  forceReload();
}

usePageMeta(() => {
  return {
    title: "Tasks",
  };
});
</script>