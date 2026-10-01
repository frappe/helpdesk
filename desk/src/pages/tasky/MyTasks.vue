<template>
  <div class="flex flex-col h-full">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg-medium text-ink-gray-9">
          {{ __("My Tasks") }}
        </div>
      </template>
    </LayoutHeader>

    <div class="flex-1 overflow-auto p-5">
      <div v-if="tasks.loading" class="flex items-center justify-center h-full">
        <div class="text-p-base text-ink-gray-6">{{ __("Loading...") }}</div>
      </div>

      <div v-else-if="tasks.error" class="flex items-center justify-center h-full">
        <div class="flex flex-col items-center gap-2">
          <AlertTriangle class="size-10 text-ink-gray-5" />
          <div class="text-p-base text-ink-gray-7">
            {{ __("Failed to load tasks. Please try again.") }}
          </div>
        </div>
      </div>

      <template v-else>
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div class="bg-surface-white border border-outline-gray-2 rounded-lg p-5 flex items-center gap-4">
            <div class="relative size-16 shrink-0">
              <svg class="size-16 -rotate-90" viewBox="0 0 36 36">
                <circle
                  cx="18" cy="18" r="15.5"
                  fill="none"
                  class="stroke-surface-gray-2"
                  stroke-width="3"
                />
                <circle
                  cx="18" cy="18" r="15.5"
                  fill="none"
                  class="stroke-ink-gray-7"
                  stroke-width="3"
                  stroke-linecap="round"
                  :stroke-dasharray="`${completionPercent} ${100 - completionPercent}`"
                  stroke-dashoffset="0"
                />
              </svg>
              <span class="absolute inset-0 flex items-center justify-center text-sm-medium text-ink-gray-9">
                {{ completionPercent }}%
              </span>
            </div>
            <div>
              <div class="text-xs text-ink-gray-5 mb-0.5">{{ __("Today's Work") }}</div>
              <div class="text-base-medium text-ink-gray-9">
                {{ completedTasks }} / {{ totalTasks }} {{ __("completed") }}
              </div>
            </div>
          </div>

          <div class="bg-surface-white border border-outline-gray-2 rounded-lg p-5">
            <div class="flex items-center gap-2 mb-1">
              <Clock class="size-4 text-ink-red-5" />
              <span class="text-xs text-ink-gray-5">{{ __("Overdue") }}</span>
            </div>
            <div class="text-xl-semibold text-ink-red-7">{{ overdueTasks.length }}</div>
          </div>

          <div class="bg-surface-white border border-outline-gray-2 rounded-lg p-5">
            <div class="flex items-center gap-2 mb-1">
              <AlertTriangle class="size-4 text-ink-amber-5" />
              <span class="text-xs text-ink-gray-5">{{ __("Cancelled") }}</span>
            </div>
            <div class="text-xl-semibold text-ink-gray-9">{{ blockedTasks.length }}</div>
          </div>
        </div>

        <div class="flex gap-2 mb-4">
          <button
            v-for="tab in filterTabs"
            :key="tab.key"
            class="px-3 py-1.5 rounded text-sm transition-colors"
            :class="activeFilter === tab.key
              ? 'bg-surface-gray-3 text-ink-gray-9'
              : 'text-ink-gray-6 hover:bg-surface-gray-2 hover:text-ink-gray-8'"
            @click="activeFilter = tab.key"
          >
            {{ __(tab.label) }}
          </button>
        </div>

        <div v-if="blockedTasks.length && activeFilter === 'Cancelled'" class="mb-6">
          <div class="bg-surface-white border border-outline-gray-2 rounded-lg">
            <div
              v-for="task in blockedTasks"
              :key="task.name"
              class="flex items-center gap-3 px-4 py-3 border-b border-outline-gray-2 last:border-b-0"
            >
              <AlertTriangle class="size-4 text-ink-red-5 shrink-0" />
              <span class="flex-1 text-sm text-ink-gray-8 truncate">
                {{ task.subject }}
              </span>
              <button
                class="text-xs text-ink-gray-6 px-2 py-1 rounded border border-outline-gray-2 hover:bg-surface-gray-2 transition-colors shrink-0"
                @click="onRequestHelp(task)"
              >
                {{ __("Request Help") }}
              </button>
            </div>
          </div>
        </div>

        <div class="bg-surface-white border border-outline-gray-2 rounded-lg overflow-hidden">
          <div
            class="flex items-center gap-4 px-4 py-2.5 border-b border-outline-gray-2 bg-surface-gray-1"
          >
            <span class="flex-1 text-xs text-ink-gray-5">{{ __("Task") }}</span>
            <span class="w-24 shrink-0 text-xs text-ink-gray-5">{{ __("Project") }}</span>
            <span class="w-20 shrink-0 text-xs text-ink-gray-5">{{ __("Category") }}</span>
            <span class="w-16 shrink-0 text-xs text-ink-gray-5">{{ __("Priority") }}</span>
            <span class="w-24 shrink-0 text-xs text-ink-gray-5">{{ __("Status") }}</span>
            <span class="w-20 shrink-0 text-xs text-ink-gray-5 text-right">{{ __("Due") }}</span>
          </div>

          <div v-if="!filteredTasks.length" class="p-6 text-center text-sm text-ink-gray-5">
            {{ __("No tasks found") }}
          </div>

          <button
            v-for="task in filteredTasks"
            :key="task.name"
            class="flex items-center gap-4 px-4 py-3 border-b border-outline-gray-2 last:border-b-0 w-full text-left hover:bg-surface-gray-1 transition-colors"
            :class="{ 'bg-ink-red-0': isOverdue(task) }"
            @click="openTaskDetail(task)"
          >
            <span
              class="flex-1 text-sm truncate"
              :class="isOverdue(task) ? 'text-ink-red-7' : 'text-ink-gray-8'"
            >
              {{ task.subject }}
            </span>
            <span class="w-24 shrink-0 text-xs text-ink-gray-6 truncate">
              {{ task.project }}
            </span>
            <span
              v-if="task.category"
              class="w-20 shrink-0 text-xs font-medium px-2 py-0.5 rounded-full"
              :class="categoryClasses(task.category)"
            >
              {{ task.category }}
            </span>
            <span v-else class="w-20 shrink-0" />
            <span class="w-16 shrink-0 flex items-center gap-1.5">
              <span
                class="size-1.5 rounded-full shrink-0"
                :class="priorityDotClass(task.priority)"
              />
              <span class="text-xs text-ink-gray-6">{{ task.priority || __("Low") }}</span>
            </span>
            <span
              class="w-24 shrink-0 text-xs font-medium px-2 py-0.5 rounded-full"
              :class="statusPillClasses(task.status)"
            >
              {{ task.status }}
            </span>
            <span class="w-20 shrink-0 text-xs text-right" :class="isOverdue(task) ? 'text-ink-red-6' : 'text-ink-gray-5'">
              {{ task.due_date || "-" }}
            </span>
          </button>
        </div>
      </template>
    </div>

    <div
      v-if="selectedTask"
      class="fixed inset-0 z-50 flex items-center justify-center bg-ink-black/30"
      @click.self="selectedTask = null"
    >
      <div class="bg-surface-white rounded-lg shadow-lg w-full max-w-lg mx-4 p-6">
        <div class="flex items-center justify-between mb-4">
          <span class="text-base-medium text-ink-gray-9">
            {{ selectedTask.subject }}
          </span>
          <button class="text-ink-gray-5 hover:text-ink-gray-7" @click="selectedTask = null">
            <X class="size-5" />
          </button>
        </div>

        <div v-if="taskDetail.loading" class="text-sm text-ink-gray-5 py-4 text-center">
          {{ __("Loading detail...") }}
        </div>
        <template v-else-if="taskDetail.data">
          <dl class="grid grid-cols-2 gap-3 text-sm">
            <div>
              <dt class="text-xs text-ink-gray-5 mb-0.5">{{ __("Status") }}</dt>
              <dd class="text-ink-gray-8">{{ taskDetail.data.status }}</dd>
            </div>
            <div>
              <dt class="text-xs text-ink-gray-5 mb-0.5">{{ __("Priority") }}</dt>
              <dd class="text-ink-gray-8">{{ taskDetail.data.priority }}</dd>
            </div>
            <div>
              <dt class="text-xs text-ink-gray-5 mb-0.5">{{ __("Project") }}</dt>
              <dd class="text-ink-gray-8">{{ taskDetail.data.project }}</dd>
            </div>
            <div>
              <dt class="text-xs text-ink-gray-5 mb-0.5">{{ __("Due Date") }}</dt>
              <dd class="text-ink-gray-8">{{ taskDetail.data.due_date || "-" }}</dd>
            </div>
            <div class="col-span-2">
              <dt class="text-xs text-ink-gray-5 mb-0.5">{{ __("Description") }}</dt>
              <dd class="text-ink-gray-8">{{ taskDetail.data.description || __("No description") }}</dd>
            </div>
          </dl>
        </template>
        <div v-else class="text-sm text-ink-gray-5 py-4 text-center">
          {{ __("Failed to load task detail.") }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { createResource } from "frappe-ui";
import { __ } from "@/translation";
import LayoutHeader from "@/components/LayoutHeader.vue";
import AlertTriangle from "~icons/lucide/alert-triangle";
import Clock from "~icons/lucide/clock";
import X from "~icons/lucide/x";

interface Task {
  name: string;
  subject: string;
  status: string;
  category?: string;
  priority?: string;
  project?: string;
  due_date?: string;
  estimated_hours?: number;
  assigned_to?: string;
  assignees?: string;
}

const tasks = createResource({
  url: "helpdesk.tasky.api.get_my_tasks",
  auto: true,
  transform: (data: Task[]) => data ?? [],
});

const taskDetail = createResource({
  url: "helpdesk.tasky.api.get_task_detail",
});

const activeFilter = ref("All");
const selectedTask = ref<Task | null>(null);

const filterTabs = [
  { key: "All", label: "All" },
  { key: "Open", label: "Open" },
  { key: "Working", label: "Working" },
  { key: "Pending Review", label: "Pending Review" },
  { key: "Completed", label: "Completed" },
  { key: "Cancelled", label: "Cancelled" },
];

const allTasks = computed<Task[]>(() => tasks.data ?? []);

function isOverdue(task: Task) {
  if (!task.due_date) return false;
  if (["Completed", "Cancelled"].includes(task.status)) return false;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return new Date(task.due_date) < today;
}

const overdueTasks = computed<Task[]>(() =>
  allTasks.value.filter((t) => isOverdue(t))
);

const blockedTasks = computed<Task[]>(() =>
  allTasks.value.filter((t) => t.status === "Cancelled")
);

const filteredTasks = computed<Task[]>(() => {
  if (activeFilter.value === "All") return allTasks.value;
  return allTasks.value.filter((t) => t.status === activeFilter.value);
});

const totalTasks = computed(() => allTasks.value.length);

const completedTasks = computed(
  () => allTasks.value.filter((t) => t.status === "Completed").length
);

const completionPercent = computed(() =>
  totalTasks.value > 0
    ? Math.round((completedTasks.value / totalTasks.value) * 100)
    : 0
);

function openTaskDetail(task: Task) {
  selectedTask.value = task;
  taskDetail.submit({ task: task.name });
}

function onRequestHelp(task: Task) {
  alert(`Request help for: ${task.subject} (coming soon)`);
}

function categoryClasses(category: string) {
  const map: Record<string, string> = {
    Functional: "bg-ink-blue-1 text-ink-blue-8",
    Development: "bg-ink-purple-1 text-ink-purple-8",
    Support: "bg-ink-green-1 text-ink-green-8",
    Common: "bg-ink-gray-2 text-ink-gray-7",
  };
  return map[category] || map.Common;
}

function priorityDotClass(priority: string) {
  const map: Record<string, string> = {
    Urgent: "bg-ink-red-5",
    High: "bg-ink-amber-5",
    Medium: "bg-ink-blue-4",
    Low: "bg-ink-gray-4",
  };
  return map[priority] || map.Low;
}

function statusPillClasses(status: string) {
  const map: Record<string, string> = {
    Open: "bg-ink-gray-2 text-ink-gray-7",
    Working: "bg-ink-amber-1 text-ink-amber-8",
    "Pending Review": "bg-ink-blue-1 text-ink-blue-8",
    Completed: "bg-ink-green-1 text-ink-green-8",
    Cancelled: "bg-ink-gray-2 text-ink-gray-7",
  };
  return map[status] || map.Open;
}
</script>
