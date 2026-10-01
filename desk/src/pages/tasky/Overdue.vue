<template>
  <div class="flex flex-col h-full">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg-medium text-ink-gray-9">{{ __("Overdue Tasks") }}</div>
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
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div class="bg-surface-white border border-outline-gray-2 rounded-lg p-4">
            <div class="flex items-center gap-2 mb-1"><AlertTriangle class="size-4 text-ink-red-5" /><span class="text-xs text-ink-gray-5">{{ __("Overdue") }}</span></div>
            <div class="text-xl-semibold text-ink-red-7">{{ overdue.length }}</div>
          </div>
          <div class="bg-surface-white border border-outline-gray-2 rounded-lg p-4">
            <div class="flex items-center gap-2 mb-1"><Clock class="size-4 text-ink-amber-5" /><span class="text-xs text-ink-gray-5">{{ __("Due This Week") }}</span></div>
            <div class="text-xl-semibold text-ink-amber-7">{{ dueThisWeek.length }}</div>
          </div>
          <div class="bg-surface-white border border-outline-gray-2 rounded-lg p-4">
            <div class="flex items-center gap-2 mb-1"><CheckCircle2 class="size-4 text-ink-green-5" /><span class="text-xs text-ink-gray-5">{{ __("On Track") }}</span></div>
            <div class="text-xl-semibold text-ink-green-7">{{ onTrack.length }}</div>
          </div>
        </div>
        <div v-if="overdue.length" class="mb-6">
          <div class="text-sm-medium text-ink-gray-7 mb-3">{{ __("Overdue Tasks") }}</div>
          <div class="bg-surface-white border border-outline-gray-2 rounded-lg overflow-hidden">
            <div v-for="task in overdue" :key="task.name" class="flex items-center gap-3 px-4 py-3 border-b border-outline-gray-2 last:border-b-0 hover:bg-surface-sidebar">
              <AlertTriangle class="size-4 text-ink-red-5 shrink-0" />
              <div class="flex-1 min-w-0"><div class="text-sm text-ink-gray-8 truncate">{{ task.subject }}</div><div class="text-xs text-ink-gray-5">{{ task.phase }} · {{ task.due_date }}</div></div>
              <span class="text-xs font-medium px-2 py-0.5 rounded-full whitespace-nowrap" :class="statusPillClasses(task.status)">{{ task.status }}</span>
              <span class="text-xs text-ink-gray-6">{{ task.assigned_to || "" }}</span>
            </div>
          </div>
        </div>
        <div v-if="dueThisWeek.length" class="mb-6">
          <div class="text-sm-medium text-ink-gray-7 mb-3">{{ __("Due This Week") }}</div>
          <div class="bg-surface-white border border-outline-gray-2 rounded-lg overflow-hidden">
            <div v-for="task in dueThisWeek" :key="task.name" class="flex items-center gap-3 px-4 py-3 border-b border-outline-gray-2 last:border-b-0 hover:bg-surface-sidebar">
              <Clock class="size-4 text-ink-amber-5 shrink-0" />
              <div class="flex-1 min-w-0"><div class="text-sm text-ink-gray-8 truncate">{{ task.subject }}</div><div class="text-xs text-ink-gray-5">{{ task.phase }} · {{ task.due_date }}</div></div>
              <span class="text-xs font-medium px-2 py-0.5 rounded-full whitespace-nowrap" :class="statusPillClasses(task.status)">{{ task.status }}</span>
            </div>
          </div>
        </div>
        <div v-if="!overdue.length && !dueThisWeek.length" class="flex items-center justify-center py-12">
          <div class="flex flex-col items-center gap-2"><CheckCircle2 class="size-12 text-ink-gray-4" /><div class="text-lg-medium text-ink-gray-6">{{ __("All tasks are on track") }}</div></div>
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
import AlertTriangle from "~icons/lucide/alert-triangle";
import Clock from "~icons/lucide/clock";
import CheckCircle2 from "~icons/lucide/check-circle-2";

const props = defineProps<{ projectId: string }>();
const route = useRoute();

const projectTabs = [
  { label: "Dashboard", to: "TaskyProject" },
  { label: "Checklist", to: "TaskyChecklist" },
  { label: "Board", to: "TaskyKanban" },
  { label: "Timeline", to: "TaskyTimeline" },
  { label: "Overdue", to: "TaskyOverdue" },
];

interface Task { name: string; subject: string; phase?: string; status: string; due_date?: string; assigned_to?: string; }
const tasks = createResource({ url: "helpdesk.tasky.api.get_project_dashboard", makeParams: () => ({ project: props.projectId }), auto: true });
watch(() => props.projectId, () => { if (props.projectId) tasks.reload(); });

const allTasks = computed<Task[]>(() => tasks.data?.tasks ?? []);
const overdue = computed<Task[]>(() => allTasks.value.filter((t) => { if (!t.due_date || ["Completed", "Cancelled"].includes(t.status)) return false; return new Date(t.due_date) < new Date(); }));
const dueThisWeek = computed<Task[]>(() => { const now = new Date(); const end = new Date(now); end.setDate(now.getDate() + 7); return allTasks.value.filter((t) => { if (!t.due_date || ["Completed", "Cancelled"].includes(t.status)) return false; const d = new Date(t.due_date); return d >= now && d <= end; }); });
const onTrack = computed<Task[]>(() => allTasks.value.filter((t) => { if (!t.due_date || ["Completed", "Cancelled"].includes(t.status)) return false; return new Date(t.due_date) >= new Date(); }));
function statusPillClasses(s: string) { const m: Record<string, string> = { Open: "bg-ink-gray-2 text-ink-gray-7", Working: "bg-ink-amber-1 text-ink-amber-8", "Pending Review": "bg-ink-blue-1 text-ink-blue-8", Completed: "bg-ink-green-1 text-ink-green-8", Cancelled: "bg-ink-gray-2 text-ink-gray-5 line-through" }; return m[s] || m.Open; }
</script>
