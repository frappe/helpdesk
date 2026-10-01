<template>
  <div class="flex flex-col h-full">
    <LayoutHeader>
      <template #left-header><div class="text-lg-medium text-ink-gray-9">{{ __("Timesheets") }}</div></template>
      <template #right-header>
        <button class="flex items-center gap-1.5 px-3 py-1.5 rounded text-sm bg-surface-gray-3 text-ink-gray-8 hover:bg-surface-gray-4 transition-colors" @click="showForm = !showForm">
          <Plus class="size-4" /> {{ __("New Timesheet") }}
        </button>
      </template>
    </LayoutHeader>
    <div class="flex-1 overflow-auto p-5">
      <div v-if="showForm" class="bg-surface-white border border-outline-gray-2 rounded-lg p-5 mb-6">
        <div class="text-sm-medium text-ink-gray-8 mb-4">{{ __("Create Timesheet") }}</div>
        <div class="grid grid-cols-2 gap-4 mb-4">
          <div class="flex flex-col gap-1 col-span-2">
            <label class="text-xs text-ink-gray-5">Title</label>
            <input v-model="form.title" class="border border-outline-gray-2 rounded px-3 py-1.5 text-sm bg-surface-white focus:outline-none" placeholder="e.g. Weekly meeting, Bug fix..." />
          </div>
          <div class="flex flex-col gap-1">
            <label class="text-xs text-ink-gray-5">Project</label>
            <select v-model="form.project" class="border border-outline-gray-2 rounded px-3 py-1.5 text-sm bg-surface-white focus:outline-none">
              <option value="">None</option>
              <option v-for="p in (projectList.data ?? [])" :key="p.name" :value="p.name">{{ p.project_name || p.name }}</option>
            </select>
          </div>
          <div class="flex flex-col gap-1">
            <label class="text-xs text-ink-gray-5">Task (optional)</label>
            <select v-model="form.task" class="border border-outline-gray-2 rounded px-3 py-1.5 text-sm bg-surface-white focus:outline-none" :disabled="!form.project">
              <option value="">None</option>
              <option v-for="t in taskList" :key="t.name" :value="t.name">{{ t.subject }}</option>
            </select>
          </div>
          <div class="flex flex-col gap-1">
            <label class="text-xs text-ink-gray-5">Hours</label>
            <input v-model.number="form.hours" type="number" step="0.25" min="0.25" class="border border-outline-gray-2 rounded px-3 py-1.5 text-sm bg-surface-white focus:outline-none" />
          </div>
          <div class="flex flex-col gap-1">
            <label class="text-xs text-ink-gray-5">Notes</label>
            <input v-model="form.notes" class="border border-outline-gray-2 rounded px-3 py-1.5 text-sm bg-surface-white focus:outline-none" />
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button class="px-4 py-1.5 rounded text-sm bg-surface-gray-3 text-ink-gray-8 hover:bg-surface-gray-4 disabled:opacity-50" :disabled="!form.title || createTs.loading" @click="onCreate">{{ createTs.loading ? "Saving..." : "Create Timesheet" }}</button>
          <button class="px-4 py-1.5 rounded text-sm text-ink-gray-6 hover:text-ink-gray-8" @click="showForm = false">Cancel</button>
        </div>
      </div>

      <div v-if="timesheets.loading" class="flex items-center justify-center h-64"><div class="text-p-base text-ink-gray-6">Loading...</div></div>
      <div v-else-if="!timesheets.data?.length" class="flex items-center justify-center h-64">
        <div class="flex flex-col items-center gap-2"><LucideClock class="size-12 text-ink-gray-4" /><div class="text-lg-medium text-ink-gray-6">No timesheets yet</div></div>
      </div>
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div v-for="ts in timesheets.data" :key="ts.name" class="bg-surface-white border border-outline-gray-2 rounded-lg p-4">
          <div class="text-sm-medium text-ink-gray-9 truncate mb-0.5">{{ ts.title || ts.name }}</div>
          <div v-if="ts.project_name || ts.projects?.length" class="text-xs text-ink-gray-5 mb-1">
            {{ ts.project_name || "" }} {{ ts.projects && ts.projects[0] ? "(" + ts.projects[0] + ")" : "" }}
          </div>
          <div class="flex items-center gap-3 text-xs text-ink-gray-5">
            <span class="px-2 py-0.5 rounded-full" :class="ts.status === 'Submitted' ? 'bg-ink-green-1 text-ink-green-8' : 'bg-ink-amber-1 text-ink-amber-8'">{{ ts.status }}</span>
            <span>{{ ts.total_hours || 0 }}h</span>
            <span>{{ formatDate(ts.modified) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, computed, watch } from "vue";
import { createResource } from "frappe-ui";
import { __ } from "@/translation";
import LayoutHeader from "@/components/LayoutHeader.vue";
import LucideClock from "~icons/lucide/clock";
import Plus from "~icons/lucide/plus";

const showForm = ref(false);

const form = reactive({ title: "", project: "", task: "", hours: 1, notes: "" });

const timesheets = createResource({
  url: "helpdesk.tasky.api.get_my_timesheets",
  auto: true,
  transform: (d: any[]) => d ?? [],
});

const projectList = createResource({
  url: "helpdesk.tasky.api.get_projects",
  auto: true,
  transform: (d: any[]) => d ?? [],
});

const taskResource = createResource({
  url: "helpdesk.tasky.api.get_project_tasks",
  auto: false,
  transform: (d: any[]) => d ?? [],
});

const taskList = computed(() => taskResource.data ?? []);

watch(() => form.project, (val) => {
  form.task = "";
  if (val) {
    taskResource.submit({ project: val });
  }
});

const createTs = createResource({
  url: "helpdesk.tasky.api.create_timesheet",
  onSuccess() {
    form.title = ""; form.project = ""; form.task = ""; form.hours = 1; form.notes = "";
    showForm.value = false;
    timesheets.reload();
  },
});

function onCreate() {
  if (!form.title) return;
  createTs.submit({
    title: form.title,
    project: form.project || null,
    task: form.task || null,
    hours: form.hours || 1,
    notes: form.notes,
  });
}

function formatDate(d: string) { return new Date(d).toLocaleDateString("en-US", { month: "short", day: "numeric" }); }
</script>
