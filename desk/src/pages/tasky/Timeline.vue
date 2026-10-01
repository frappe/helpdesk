<template>
  <div class="flex flex-col h-full">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg-medium text-ink-gray-9">{{ __("Timeline") }}</div>
      </template>
      <template #right-header>
        <div class="flex items-center gap-1">
          <router-link v-for="tab in projectTabs" :key="tab.to" :to="{ name: tab.to, params: { projectId } }"
            class="px-3 py-1.5 rounded text-sm transition-colors"
            :class="route.name === tab.to ? 'bg-surface-gray-3 text-ink-gray-9' : 'text-ink-gray-6 hover:bg-surface-gray-2 hover:text-ink-gray-8'">
            {{ __(tab.label) }}
          </router-link>
        </div>
      </template>
    </LayoutHeader>
    <div class="flex-1 overflow-auto p-5">
      <div v-if="tasks.loading" class="flex items-center justify-center h-full"><div class="text-p-base text-ink-gray-6">{{ __("Loading...") }}</div></div>
      <template v-else>
        <div class="bg-surface-white border border-outline-gray-2 rounded-lg overflow-hidden mb-4">
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead><tr class="border-b border-outline-gray-2 bg-surface-gray-1">
                <th class="text-left px-4 py-2.5 text-xs text-ink-gray-5 font-medium">{{ __("Task") }}</th>
                <th class="text-left px-4 py-2.5 text-xs text-ink-gray-5 font-medium w-24">{{ __("Phase") }}</th>
                <th class="text-left px-4 py-2.5 text-xs text-ink-gray-5 font-medium w-24">{{ __("Status") }}</th>
                <th class="text-left px-4 py-2.5 text-xs text-ink-gray-5 font-medium w-28">{{ __("Due Date") }}</th>
                <th class="text-left px-4 py-2.5 text-xs text-ink-gray-5 font-medium w-24">{{ __("Priority") }}</th>
              </tr></thead>
              <tbody>
                <tr v-for="task in sortedTasks" :key="task.name" class="border-b border-outline-gray-2 hover:bg-surface-sidebar"
                  :class="{ 'bg-ink-red-0': isOverdue(task) }">
                  <td class="px-4 py-2.5">
                    <div class="flex items-center gap-2">
                      <span class="size-1.5 rounded-full shrink-0" :class="priorityDotClass(task.priority)" />
                      <span class="text-ink-gray-8 truncate">{{ task.subject }}</span>
                      <span v-if="isOverdue(task)" class="text-xs text-ink-red-6 font-medium">{{ __("Overdue") }}</span>
                    </div>
                  </td>
                  <td class="px-4 py-2.5 text-ink-gray-6">{{ task.phase || "-" }}</td>
                  <td class="px-4 py-2.5"><span class="text-xs font-medium px-2 py-0.5 rounded-full whitespace-nowrap" :class="statusPillClasses(task.status)">{{ task.status }}</span></td>
                  <td class="px-4 py-2.5 text-ink-gray-6">{{ task.due_date || "-" }}</td>
                  <td class="px-4 py-2.5">{{ task.priority }}</td>
                </tr>
                <tr v-if="sortedTasks.length === 0"><td colspan="5" class="px-4 py-8 text-center text-sm text-ink-gray-5">{{ __("No tasks in this project") }}</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, watch } from "vue";
import { useRoute } from "vue-router";
import { createResource } from "frappe-ui";
import { __ } from "@/translation";
import LayoutHeader from "@/components/LayoutHeader.vue";

const props = defineProps<{ projectId: string }>();
const route = useRoute();

const projectTabs = [
  { label: "Dashboard", to: "TaskyProject" },
  { label: "Checklist", to: "TaskyChecklist" },
  { label: "Board", to: "TaskyKanban" },
  { label: "Timeline", to: "TaskyTimeline" },
  { label: "Overdue", to: "TaskyOverdue" },
];

interface Task { name: string; subject: string; phase?: string; status: string; priority?: string; due_date?: string; }
const tasks = createResource({ url: "helpdesk.tasky.api.get_project_dashboard", makeParams: () => ({ project: props.projectId }), auto: true });
watch(() => props.projectId, () => { if (props.projectId) tasks.reload(); });

const sortedTasks = computed<Task[]>(() => {
  const list = tasks.data?.tasks ?? [];
  return [...list].sort((a, b) => { if (!a.due_date) return 1; if (!b.due_date) return -1; return new Date(a.due_date).getTime() - new Date(b.due_date).getTime(); });
});
function isOverdue(t: Task) { if (!t.due_date || ["Completed", "Cancelled"].includes(t.status)) return false; return new Date(t.due_date) < new Date(); }
function statusPillClasses(s: string) { const m: Record<string, string> = { Open: "bg-ink-gray-2 text-ink-gray-7", Working: "bg-ink-amber-1 text-ink-amber-8", "Pending Review": "bg-ink-blue-1 text-ink-blue-8", Completed: "bg-ink-green-1 text-ink-green-8", Cancelled: "bg-ink-gray-2 text-ink-gray-5 line-through" }; return m[s] || m.Open; }
function priorityDotClass(p: string) { const m: Record<string, string> = { Urgent: "bg-ink-red-5", High: "bg-ink-amber-5", Medium: "bg-ink-blue-4", Low: "bg-ink-gray-4" }; return m[p] || m.Low; }
</script>
