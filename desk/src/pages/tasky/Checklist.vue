<template>
  <div class="flex flex-col h-full">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg-medium text-ink-gray-9">{{ __("Checklist") }}</div>
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
    <div class="flex-1 overflow-auto p-4">
      <div class="bg-surface-white border border-outline-gray-2 rounded-lg p-4 mb-4">
        <div class="text-sm-medium text-ink-gray-8 mb-3">{{ __("Add Task") }}</div>
        <div class="flex items-center gap-2 flex-wrap">
          <input v-model="newTask.task_name" placeholder="Task name" class="flex-1 min-w-[200px] border border-outline-gray-2 rounded px-3 py-1.5 text-sm bg-surface-white focus:outline-none focus:border-outline-gray-3" @keyup.enter="onAddTask" />
          <input v-model="newTask.phase" placeholder="Phase" class="w-28 border border-outline-gray-2 rounded px-2 py-1.5 text-sm bg-surface-white focus:outline-none focus:border-outline-gray-3" />
          <select v-model="newTask.category" class="w-28 border border-outline-gray-2 rounded px-2 py-1.5 text-sm bg-surface-white">
            <option>Functional</option><option>Development</option><option>Support</option><option>Common</option>
          </select>
          <select v-model="newTask.priority" class="w-24 border border-outline-gray-2 rounded px-2 py-1.5 text-sm bg-surface-white">
            <option>High</option><option>Medium</option><option>Low</option><option>Urgent</option>
          </select>
          <select v-model="newTask.assigned_to" class="w-44 border border-outline-gray-2 rounded px-2 py-1.5 text-sm bg-surface-white">
            <option value="">Unassigned</option>
            <option v-for="u in projectMembers" :key="u.user" :value="u.user">{{ u.full_name || u.user }}</option>
          </select>
          <input v-model.number="newTask.estimated_hours" type="number" placeholder="Hrs" class="w-16 border border-outline-gray-2 rounded px-2 py-1.5 text-sm bg-surface-white" />
          <input v-model="newTask.due_date" type="date" class="w-32 border border-outline-gray-2 rounded px-2 py-1.5 text-sm bg-surface-white" />
          <button class="px-4 py-1.5 text-sm rounded bg-surface-gray-8 text-ink-white hover:bg-surface-gray-9 disabled:opacity-50 font-medium" :disabled="!newTask.task_name || addTask.loading" @click="onAddTask">{{ addTask.loading ? "Adding..." : "+ Add Task" }}</button>
        </div>
      </div>
      <div v-if="phases.loading" class="flex items-center justify-center py-12">
        <LoadingIndicator :scale="4" />
      </div>
      <template v-else-if="phases.data?.phases">
        <div v-for="phase in phases.data.phases" :key="phase.name" class="border border-outline-gray-2 rounded-lg bg-surface-white overflow-hidden mb-3">
          <button class="flex items-center justify-between w-full p-4 hover:bg-surface-sidebar transition-colors" @click="togglePhase(phase.phase_name)">
            <div class="flex items-center gap-3">
              <component :is="expandedPhases.has(phase.phase_name) ? LucideChevronDown : LucideChevronRight" class="size-4 text-ink-gray-6 flex-shrink-0" />
              <span class="text-base-medium text-ink-gray-9">{{ phase.phase_name || phase.name }}</span>
            </div>
            <div class="flex items-center gap-3">
              <div class="flex items-center gap-2">
                <div class="w-24 h-2 bg-surface-gray-2 rounded-full overflow-hidden">
                  <div class="h-full bg-ink-blue-4 rounded-full transition-all" :style="{ width: `${phase.progress_pct || 0}%` }" />
                </div>
                <span class="text-sm text-ink-gray-6 whitespace-nowrap">{{ phase.completed_count || 0 }}/{{ phase.total_count || 0 }}</span>
              </div>
            </div>
          </button>
          <div v-if="expandedPhases.has(phase.phase_name)" class="border-t border-outline-gray-2">
            <div v-if="phaseTasks[phase.phase_name]?.loading" class="flex items-center justify-center py-6"><LoadingIndicator :scale="3" /></div>
            <template v-else-if="phaseTasks[phase.phase_name]?.data">
               <div v-for="task in phaseTasks[phase.phase_name].data" :key="task.name" class="flex items-center gap-3 px-4 py-3 hover:bg-surface-sidebar border-b border-outline-gray-2 last:border-b-0" :class="{ 'bg-ink-red-0': isOverdue(task) }">
                <button class="flex-shrink-0 size-5 rounded border-2 flex items-center justify-center transition-colors"
                  :class="task.status === 'Completed' ? 'bg-ink-blue-4 border-ink-blue-4 text-white' : 'border-outline-gray-3 hover:border-outline-gray-4 text-transparent'"
                  @click="onToggleTask(task)">
                  <LucideCheck v-if="task.status === 'Completed'" class="size-3" />
                </button>
                 <span class="flex-1 text-sm truncate" :class="isOverdue(task) ? 'text-ink-red-7' : task.status === 'Completed' ? 'text-ink-gray-5 line-through' : 'text-ink-gray-8'">{{ task.subject }}</span>
                <span v-if="task.due_date" class="text-xs whitespace-nowrap flex items-center gap-1" :class="isOverdue(task) ? 'text-ink-red-6 font-medium' : 'text-ink-gray-5'"><LucideClock class="size-3" /> {{ formatDate(task.start_date) || formatDate(task.due_date) }} - {{ formatDate(task.due_date) }}<span v-if="isOverdue(task)" class="ml-1">Overdue</span></span>
                <span v-if="task.category" class="text-xs font-medium px-2 py-0.5 rounded-full whitespace-nowrap" :class="categoryClasses(task.category)">{{ task.category }}</span>
                <div v-if="task.assigned_to" class="flex-shrink-0"><UserAvatar :name="task.assigned_to" size="sm" :hide-avatar="false" /></div>
                <span class="flex-shrink-0 size-1.5 rounded-full" :class="priorityDotClass(task.priority)" />
                <span class="text-xs font-medium px-2 py-0.5 rounded-full whitespace-nowrap" :class="statusPillClasses(task.status)">{{ task.status }}</span>
              </div>
            </template>
            <div v-else class="flex items-center justify-center py-8 text-sm text-ink-gray-5">{{ __("No tasks in this phase") }}</div>
          </div>
        </div>
      </template>
      <div v-else class="flex items-center justify-center py-12 text-sm text-ink-gray-5">{{ __("No phases found") }}</div>
    </div>

    <div v-if="completingTask" class="fixed inset-0 z-50 flex items-center justify-center bg-black/25 backdrop-blur-sm" @click.self="completingTask = null">
      <div class="bg-surface-white border border-outline-gray-2 rounded-xl shadow-xl w-full max-w-sm p-5">
        <div class="text-base-semibold text-ink-gray-9 mb-1">{{ __("Complete Task") }}</div>
        <div class="text-sm text-ink-gray-6 mb-4 truncate">{{ completingTask.subject }}</div>
        <div class="flex flex-col gap-3 mb-4">
          <div class="flex flex-col gap-1">
            <label class="text-xs text-ink-gray-5">{{ __("Hours Worked") }}</label>
            <input v-model.number="completeHours" type="number" step="0.5" min="0" class="border border-outline-gray-2 rounded px-3 py-1.5 text-sm bg-surface-white focus:outline-none" placeholder="e.g. 2.5" />
          </div>
          <div class="flex flex-col gap-1">
            <label class="text-xs text-ink-gray-5">{{ __("Notes") }}</label>
            <input v-model="completeNotes" class="border border-outline-gray-2 rounded px-3 py-1.5 text-sm bg-surface-white focus:outline-none" placeholder="What was done?" />
          </div>
        </div>
        <div class="flex justify-end gap-2">
          <button @click="completingTask = null" class="px-4 py-2 text-sm text-ink-gray-7 hover:bg-surface-gray-2 rounded-lg">{{ __("Cancel") }}</button>
          <button @click="confirmComplete" class="px-5 py-2 text-sm font-medium rounded-lg bg-ink-gray-9 text-ink-white hover:bg-ink-gray-8">{{ __("Mark Complete") }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { createResource } from "frappe-ui";
import { reactive, computed, ref } from "vue";
import { useRoute } from "vue-router";
import { __ } from "@/translation";
import LayoutHeader from "@/components/LayoutHeader.vue";
import { UserAvatar } from "@/components";
import LucideChevronDown from "~icons/lucide/chevron-down";
import LucideChevronRight from "~icons/lucide/chevron-right";
import LucideCheck from "~icons/lucide/check";
import LucideClock from "~icons/lucide/clock";

const props = defineProps<{ projectId: string }>();
const route = useRoute();

const projectTabs = [
  { label: "Dashboard", to: "TaskyProject" },
  { label: "Checklist", to: "TaskyChecklist" },
  { label: "Board", to: "TaskyKanban" },
  { label: "Timeline", to: "TaskyTimeline" },
  { label: "Overdue", to: "TaskyOverdue" },
];

const expandedPhases = reactive<Set<string>>(new Set());
const phaseTasks: Record<string, ReturnType<typeof createResource>> = reactive({});

const phases = createResource({ url: "helpdesk.tasky.api.get_project_dashboard", makeParams: () => ({ project: props.projectId }), auto: true });

const projectDetail = createResource({ url: "helpdesk.tasky.api.get_project_detail", makeParams: () => ({ project: props.projectId }), auto: true });

const projectMembers = computed(() => projectDetail.data?.users ?? []);

const newTask = reactive({ task_name: "", phase: "", category: "Functional", priority: "Medium", estimated_hours: 0, assigned_to: "", due_date: "" });

const addTask = createResource({
  url: "helpdesk.tasky.api.add_task",
  onSuccess() {
    newTask.task_name = "";
    newTask.phase = "";
    newTask.category = "Functional";
    newTask.priority = "Medium";
    newTask.estimated_hours = 0;
    newTask.assigned_to = "";
    newTask.due_date = "";
    phases.reload();
  },
});

const updateTaskStatus = createResource({ url: "helpdesk.tasky.api.update_task_status" });
const completeResource = createResource({
  url: "helpdesk.tasky.api.complete_task",
  onError(e: any) { alert("Failed to complete: " + (e?.message || e)); },
});

const completingTask = ref<any>(null);
const completeHours = ref(0);
const completeNotes = ref("");

function onAddTask() {
  if (!newTask.task_name) return;
  addTask.submit({
    project: props.projectId,
    task_name: newTask.task_name,
    phase: newTask.phase,
    category: newTask.category,
    priority: newTask.priority,
    estimated_hours: newTask.estimated_hours,
    assigned_to: newTask.assigned_to,
    due_date: newTask.due_date || null,
  });
}

function togglePhase(phaseName: string) {
  if (expandedPhases.has(phaseName)) { expandedPhases.delete(phaseName); return; }
  expandedPhases.add(phaseName);
  if (!phaseTasks[phaseName]) {
    phaseTasks[phaseName] = createResource({ url: "helpdesk.tasky.api.get_phase_tasks", makeParams: () => ({ project: props.projectId, phase: phaseName }), auto: true });
  }
}

function onToggleTask(task: Record<string, any>) {
  if (task.status === "Completed") {
    updateTaskStatus.submit({ task: task.name, status: "Open" });
    task.status = "Open";
    return;
  }
  completingTask.value = task;
  completeHours.value = task.estimated_hours || 0;
  completeNotes.value = "";
}

function confirmComplete() {
  const task = completingTask.value;
  if (!task) return;
  completeResource.submit({
    task: task.name,
    hours_worked: completeHours.value || 0.25,
    notes: completeNotes.value,
  });
  task.status = "Completed";
  completingTask.value = null;
  phases.reload();
}

function categoryClasses(c: string) {
  const m: Record<string, string> = { Functional: "bg-ink-blue-1 text-ink-blue-8", Development: "bg-ink-purple-1 text-ink-purple-8", Support: "bg-ink-green-1 text-ink-green-8", Common: "bg-ink-gray-2 text-ink-gray-7" };
  return m[c] || m.Common;
}
function priorityDotClass(p: string) {
  const m: Record<string, string> = { Urgent: "bg-ink-red-5", High: "bg-ink-amber-5", Medium: "bg-ink-blue-4", Low: "bg-ink-gray-4" };
  return m[p] || m.Low;
}
function statusPillClasses(s: string) {
  const m: Record<string, string> = { Open: "bg-ink-gray-2 text-ink-gray-7", Working: "bg-ink-amber-1 text-ink-amber-8", "Pending Review": "bg-ink-blue-1 text-ink-blue-8", Completed: "bg-ink-green-1 text-ink-green-8", Cancelled: "bg-ink-gray-2 text-ink-gray-5 line-through" };
  return m[s] || m.Open;
}
function isOverdue(t: Record<string, any>) {
  if (!t.due_date || ["Completed", "Cancelled"].includes(t.status)) return false;
  return new Date(t.due_date) < new Date();
}
function formatDate(d: string) {
  return new Date(d).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}
</script>
