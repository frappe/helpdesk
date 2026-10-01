<template>
  <div class="flex flex-col h-full">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg-medium text-ink-gray-9">{{ editing ? editTitle : __("Templates") }}</div>
      </template>
      <template #right-header>
        <button v-if="!editing" class="flex items-center gap-1.5 px-3 py-1.5 rounded text-sm bg-surface-gray-3 text-ink-gray-8 hover:bg-surface-gray-4 transition-colors" @click="startNew">
          <Plus class="size-4" /> {{ __("New Template") }}
        </button>
        <button v-else class="flex items-center gap-1.5 px-3 py-1.5 rounded text-sm text-ink-gray-6 hover:text-ink-gray-9 transition-colors" @click="cancelEdit">
          <LucideX class="size-4" /> {{ __("Close") }}
        </button>
      </template>
    </LayoutHeader>

    <div class="flex-1 overflow-auto p-5">
      <div v-if="editing" class="bg-surface-white border border-outline-gray-2 rounded-lg p-5 mb-6">
        <div class="grid grid-cols-2 gap-4 mb-4">
          <div class="flex flex-col gap-1">
            <label class="text-xs text-ink-gray-5">Template Name</label>
            <input v-model="form.template_name" class="border border-outline-gray-2 rounded px-3 py-1.5 text-sm bg-surface-white focus:outline-none focus:border-outline-gray-3" />
          </div>
          <div class="flex flex-col gap-1">
            <label class="text-xs text-ink-gray-5">Industry</label>
            <input v-model="form.industry" class="border border-outline-gray-2 rounded px-3 py-1.5 text-sm bg-surface-white focus:outline-none focus:border-outline-gray-3" />
          </div>
          <div class="flex flex-col gap-1 col-span-2">
            <label class="text-xs text-ink-gray-5">Description</label>
            <textarea v-model="form.description" rows="2" class="border border-outline-gray-2 rounded px-3 py-1.5 text-sm bg-surface-white focus:outline-none focus:border-outline-gray-3" />
          </div>
        </div>

        <div class="text-xs font-medium text-ink-gray-6 mb-2">Tasks</div>
        <div class="bg-surface-gray-1 rounded-lg p-1 mb-3">
          <div v-for="(group, phase) in phaseGroups" :key="phase" class="mb-0.5 last:mb-0">
            <button class="flex items-center gap-2 w-full px-3 py-2 hover:bg-surface-gray-2 rounded-lg transition-colors text-left" @click="togglePhase(phase)">
              <component :is="expandedPhases.has(phase) ? LucideChevronDown : LucideChevronRight" class="size-4 text-ink-gray-5 shrink-0" />
              <span class="text-sm-medium text-ink-gray-7">{{ phase || "Uncategorized" }}</span>
              <span class="text-xs text-ink-gray-4">({{ group.length }})</span>
              <button class="ml-auto size-5 flex items-center justify-center rounded text-ink-gray-4 hover:text-ink-red-6 transition-colors" @click.stop="removePhaseGroup(phase)"><LucideTrash class="size-3" /></button>
            </button>
            <div v-if="expandedPhases.has(phase)" class="px-2 pb-1">
              <div v-for="(task, idx) in group" :key="task._key" class="flex items-center gap-2 mb-1.5">
                <input v-model="task.task_name" placeholder="Task name" class="flex-1 border border-outline-gray-2 rounded px-2 py-1 text-sm bg-surface-white focus:outline-none" />
                <select v-model="task.category" class="w-28 border border-outline-gray-2 rounded px-2 py-1 text-sm bg-surface-white"><option>Functional</option><option>Development</option><option>Support</option><option>Common</option></select>
                <select v-model="task.default_priority" class="w-20 border border-outline-gray-2 rounded px-2 py-1 text-sm bg-surface-white"><option>High</option><option>Medium</option><option>Low</option><option>Urgent</option></select>
                <input v-model.number="task.estimated_hours" type="number" placeholder="Hrs" class="w-14 border border-outline-gray-2 rounded px-2 py-1 text-sm bg-surface-white" />
                <button @click="removeTaskFromGroup(phase, idx)" class="size-6 flex items-center justify-center rounded text-ink-gray-5 hover:text-ink-red-6"><LucideX class="size-3.5" /></button>
              </div>
            </div>
          </div>
          <div class="flex items-center gap-2 px-3 py-2">
            <input v-model="newTaskName" placeholder="New task" class="flex-1 border border-outline-gray-2 rounded px-2 py-1 text-sm bg-surface-white focus:outline-none" @keyup.enter="addTaskToPhase" />
            <input v-model="newTaskPhase" placeholder="Phase" class="w-28 border border-outline-gray-2 rounded px-2 py-1 text-sm bg-surface-white focus:outline-none" />
            <button @click="addTaskToPhase" class="flex items-center gap-1 text-xs text-ink-gray-5 hover:text-ink-gray-8 px-2 py-1"><LucidePlus class="size-3.5" /> Add</button>
          </div>
        </div>

        <div class="flex items-center gap-2">
          <button class="px-4 py-1.5 rounded text-sm bg-surface-gray-3 text-ink-gray-8 hover:bg-surface-gray-4 disabled:opacity-50" :disabled="!form.template_name || save.loading" @click="onSave">
            {{ save.loading ? "Saving..." : editingId ? "Update Template" : "Create Template" }}
          </button>
          <button class="px-4 py-1.5 rounded text-sm text-ink-gray-6 hover:text-ink-gray-8" @click="cancelEdit">Cancel</button>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" v-if="!editing">
        <button v-for="t in templates.data" :key="t.name" class="bg-surface-white border border-outline-gray-2 rounded-lg p-5 hover:shadow-md transition-shadow text-left w-full group" @click="startEdit(t.name)">
          <div class="text-base-semibold text-ink-gray-9 mb-1">{{ t.template_name }}</div>
          <div class="text-xs text-ink-gray-5 mb-3">{{ t.industry || "General" }} · {{ t.description || "No description" }}</div>
          <div class="flex items-center justify-between">
            <span class="text-xs text-ink-gray-6 bg-surface-gray-1 px-2 py-0.5 rounded-full">{{ t.name }}</span>
            <span class="text-xs text-ink-gray-4 opacity-0 group-hover:opacity-100 transition-opacity">Click to edit →</span>
          </div>
        </button>
        <div v-if="!templates.loading && !templates.data?.length" class="col-span-full flex items-center justify-center py-12">
          <div class="flex flex-col items-center gap-2"><ClipboardList class="size-12 text-ink-gray-4" /><div class="text-lg-medium text-ink-gray-6">No templates yet</div></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from "vue";
import { createResource } from "frappe-ui";
import { __ } from "@/translation";
import LayoutHeader from "@/components/LayoutHeader.vue";
import Plus from "~icons/lucide/plus";
import LucideX from "~icons/lucide/x";
import LucidePlus from "~icons/lucide/plus";
import LucideChevronDown from "~icons/lucide/chevron-down";
import LucideChevronRight from "~icons/lucide/chevron-right";
import LucideTrash from "~icons/lucide/trash-2";
import ClipboardList from "~icons/lucide/clipboard-list";

const editing = ref(false);
const editingId = ref("");
const newTaskName = ref("");
const newTaskPhase = ref("");
const expandedPhases = reactive<Set<string>>(new Set());

const templates = createResource({ url: "helpdesk.tasky.api.get_templates", auto: true, transform: (d: any) => d ?? [] });

const form = reactive<{ template_name: string; industry: string; description: string; tasks: any[] }>({
  template_name: "", industry: "", description: "", tasks: [],
});

let _taskCounter = 0;

const phaseGroups = computed(() => {
  const groups: Record<string, any[]> = {};
  for (const t of form.tasks) {
    const p = t.phase_name || "";
    if (!groups[p]) groups[p] = [];
    groups[p].push(t);
  }
  // Auto-expand all phases when editing
  for (const key of Object.keys(groups)) {
    if (!expandedPhases.has(key)) expandedPhases.add(key);
  }
  return groups;
});

const editTitle = computed(() => editingId.value ? `Edit: ${form.template_name}` : "New Template");

const detail = createResource({
  url: "helpdesk.tasky.api.get_template",
  onSuccess(data: any) {
    form.template_name = data.template_name;
    form.industry = data.industry;
    form.description = data.description;
    form.tasks = data.tasks.map((t: any) => ({ ...t, _key: String(++_taskCounter) }));
    expandedPhases.clear();
    for (const t of form.tasks) { if (!expandedPhases.has(t.phase_name || "")) expandedPhases.add(t.phase_name || ""); }
    editing.value = true;
  },
});

function startEdit(name: string) {
  editingId.value = name;
  detail.submit({ template: name });
}

function startNew() {
  form.template_name = ""; form.industry = ""; form.description = ""; form.tasks = [];
  expandedPhases.clear();
  editing.value = true;
  editingId.value = "";
}

function cancelEdit() {
  editing.value = false;
  editingId.value = "";
  form.tasks = [];
}

function togglePhase(phase: string) {
  if (expandedPhases.has(phase)) expandedPhases.delete(phase);
  else expandedPhases.add(phase);
}

function addTaskToPhase() {
  if (!newTaskName.value) return;
  form.tasks.push({
    task_name: newTaskName.value,
    phase_name: newTaskPhase.value || "",
    category: "Functional",
    default_priority: "Medium",
    estimated_hours: 0,
    _key: String(++_taskCounter),
  });
  const p = newTaskPhase.value || "";
  if (!expandedPhases.has(p)) expandedPhases.add(p);
  newTaskName.value = "";
  newTaskPhase.value = "";
}

function removeTaskFromGroup(phase: string, idx: number) {
  const tasks = phaseGroups.value[phase];
  if (!tasks) return;
  const task = tasks[idx];
  const globalIdx = form.tasks.indexOf(task);
  if (globalIdx !== -1) form.tasks.splice(globalIdx, 1);
}

function removePhaseGroup(phase: string) {
  form.tasks = form.tasks.filter((t: any) => (t.phase_name || "") !== phase);
  expandedPhases.delete(phase);
}

const save = createResource({
  url: editingId.value ? "helpdesk.tasky.api.update_template" : "helpdesk.tasky.api.create_template",
  onSuccess() {
    editing.value = false;
    editingId.value = "";
    form.tasks = [];
    templates.reload();
  },
});

function onSave() {
  const payload = {
    template_name: form.template_name,
    industry: form.industry,
    description: form.description,
    tasks: form.tasks.filter((t: any) => t.task_name),
  };
  if (editingId.value) {
    save.url = "helpdesk.tasky.api.update_template";
    save.submit({ template: editingId.value, ...payload });
  } else {
    save.url = "helpdesk.tasky.api.create_template";
    save.submit(payload);
  }
}
</script>
