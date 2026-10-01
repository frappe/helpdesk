<template>
  <div class="flex flex-col h-full">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg-medium text-ink-gray-9">
          {{ __("Projects") }}
        </div>
      </template>
      <template #right-header>
        <button
          class="flex items-center gap-1.5 px-3 py-1.5 rounded text-sm bg-surface-gray-3 text-ink-gray-8 hover:bg-surface-gray-4 transition-colors"
          @click="showNewForm = !showNewForm"
        >
          <Plus class="size-4" />
          <span>{{ __("New Project") }}</span>
        </button>
      </template>
    </LayoutHeader>

    <div class="flex-1 overflow-auto p-5">
      <div
        v-if="showNewForm"
        class="bg-surface-white border border-outline-gray-2 rounded-lg p-5 mb-6"
      >
        <div class="text-sm-medium text-ink-gray-8 mb-4">{{ __("New Project") }}</div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div class="flex flex-col gap-1">
            <label class="text-xs text-ink-gray-5">{{ __("Project Name") }}</label>
            <input
              v-model="newProject.project_name"
              class="border border-outline-gray-2 rounded px-3 py-1.5 text-sm text-ink-gray-9 bg-surface-white placeholder-ink-gray-4 focus:outline-none focus:border-outline-gray-3"
              placeholder="Enter project name"
            />
          </div>
          <div class="flex flex-col gap-1">
            <label class="text-xs text-ink-gray-5">{{ __("Start Date") }}</label>
            <input
              v-model="newProject.start_date"
              type="date"
              class="border border-outline-gray-2 rounded px-3 py-1.5 text-sm text-ink-gray-9 bg-surface-white focus:outline-none focus:border-outline-gray-3"
            />
          </div>
          <div class="flex flex-col gap-1">
            <label class="text-xs text-ink-gray-5">{{ __("Expected End Date") }}</label>
            <input
              v-model="newProject.expected_end_date"
              type="date"
              class="border border-outline-gray-2 rounded px-3 py-1.5 text-sm text-ink-gray-9 bg-surface-white focus:outline-none focus:border-outline-gray-3"
            />
          </div>
          <div class="flex flex-col gap-1 md:col-span-2">
            <label class="text-xs font-medium text-ink-gray-6 mb-1">{{ __("Team Members") }}</label>
            <div class="bg-surface-gray-1 rounded-lg p-3">
              <div v-for="(member, idx) in newProject.members" :key="idx" class="flex items-center gap-2 mb-2 last:mb-0">
                <select v-model="member.user" class="flex-1 border border-outline-gray-2 rounded px-2 py-1 text-sm bg-surface-white">
                  <option value="">Select user...</option>
                  <option v-for="u in (userList.data ?? [])" :key="u.name" :value="u.name">{{ u.full_name || u.name }}</option>
                </select>
                <select v-model="member.custom_role" class="w-40 border border-outline-gray-2 rounded px-2 py-1 text-sm bg-surface-white">
                  <option value="">Manager (no role)</option>
                  <option value="Functional Consultant">Functional Consultant</option>
                  <option value="Developer">Developer</option>
                  <option value="Support Engineer">Support Engineer</option>
                </select>
                <button @click="newProject.members.splice(idx, 1)" class="size-6 flex items-center justify-center rounded text-ink-gray-5 hover:text-ink-red-6"><LucideX class="size-3.5" /></button>
              </div>
              <button @click="newProject.members.push({ user: '', custom_role: '' })" class="flex items-center gap-1 text-xs text-ink-gray-5 hover:text-ink-gray-8"><LucidePlus class="size-3.5" /> Add member</button>
            </div>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button
            class="px-4 py-1.5 rounded text-sm bg-surface-gray-3 text-ink-gray-8 hover:bg-surface-gray-4 transition-colors disabled:opacity-50"
            :disabled="createProject.loading"
            @click="onCreateProject"
          >
            {{ createProject.loading ? __("Creating...") : __("Create") }}
          </button>
          <button
            class="px-4 py-1.5 rounded text-sm text-ink-gray-6 hover:text-ink-gray-8 transition-colors"
            @click="showNewForm = false"
          >
            {{ __("Cancel") }}
          </button>
        </div>
      </div>

      <div v-if="projects.loading" class="flex items-center justify-center h-64">
        <div class="text-p-base text-ink-gray-6">{{ __("Loading...") }}</div>
      </div>

      <div v-else-if="projects.error" class="flex items-center justify-center h-64">
        <div class="flex flex-col items-center gap-2">
          <AlertTriangle class="size-10 text-ink-gray-5" />
          <div class="text-p-base text-ink-gray-7">
            {{ __("Failed to load projects. Please try again.") }}
          </div>
        </div>
      </div>

      <div
        v-else-if="!projects.data?.length"
        class="flex items-center justify-center h-64"
      >
        <div class="flex flex-col items-center gap-2">
          <FolderKanban class="size-12 text-ink-gray-4" />
          <div class="text-lg-medium text-ink-gray-8">{{ __("No projects yet") }}</div>
          <div class="text-p-base text-ink-gray-6">
            {{ __("Create your first project to get started.") }}
          </div>
        </div>
      </div>

      <template v-else>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          <div
            v-for="project in projects.data"
            :key="project.name"
            class="bg-surface-white border border-outline-gray-2 rounded-xl overflow-hidden hover:shadow-md transition-all duration-200"
          >
            <button
              class="w-full text-left p-5 flex items-start justify-between group"
              @click="toggleExpand(project.name)"
            >
              <div class="flex-1 min-w-0 mr-3">
                <div class="flex items-center gap-2 mb-0.5">
                  <span class="text-base-semibold text-ink-gray-9 truncate">{{ project.project_name }}</span>
                  <component
                    :is="expandedCards.has(project.name) ? LucideChevronUp : LucideChevronDown"
                    class="size-4 text-ink-gray-4 shrink-0 transition-transform"
                  />
                </div>
                <div class="flex items-center gap-2 text-xs text-ink-gray-5">
                  <span class="font-mono text-ink-gray-4">{{ project.name }}</span>
                  <span v-if="formatDateRange(project)">· {{ formatDateRange(project) }}</span>
                  <span v-if="dashboards[project.name]?.data" class="text-ink-gray-6 font-medium">· {{ dashboards[project.name].data.stats.completion_pct }}%</span>
                </div>
              </div>
              <span class="text-xs font-medium px-2.5 py-1 rounded-full shrink-0" :class="statusBadgeClass(project.status)">
                {{ project.status || "Open" }}
              </span>
            </button>

            <div v-if="expandedCards.has(project.name)" class="px-5 pb-5 border-t border-outline-gray-2 pt-4">
              <div class="mb-4" v-if="dashboards[project.name]?.data">
                <div class="flex items-center justify-between mb-1.5">
                  <span class="text-xs text-ink-gray-5 font-medium">Progress</span>
                  <span class="text-xs text-ink-gray-7 font-medium">
                    {{ dashboards[project.name].data.stats.completed }}/{{ dashboards[project.name].data.stats.total }} tasks
                  </span>
                </div>
                <div class="w-full h-2.5 rounded-full bg-surface-gray-2 overflow-hidden flex">
                  <div v-if="segments(project).completed_pct > 0" class="h-full bg-ink-green-5 rounded-l-full" :style="{ width: segments(project).completed_pct + '%' }" />
                  <div v-if="segments(project).working_pct > 0" class="h-full bg-ink-amber-5" :style="{ width: segments(project).working_pct + '%' }" />
                  <div v-if="segments(project).review_pct > 0" class="h-full bg-ink-blue-4" :style="{ width: segments(project).review_pct + '%' }" />
                  <div v-if="segments(project).cancelled_pct > 0" class="h-full bg-ink-red-5" :style="{ width: segments(project).cancelled_pct + '%' }" />
                  <div v-if="segments(project).rest_pct > 0" class="h-full bg-ink-gray-4 rounded-r-full" :style="{ width: segments(project).rest_pct + '%' }" />
                </div>
                <div class="flex flex-wrap items-center gap-x-4 gap-y-1 mt-2 text-xs text-ink-gray-5">
                  <span class="flex items-center gap-1.5"><span class="size-2 rounded-full bg-ink-green-5" /> {{ dashboards[project.name].data.stats.completed }} done</span>
                  <span class="flex items-center gap-1.5"><span class="size-2 rounded-full bg-ink-amber-5" /> {{ dashboards[project.name].data.stats.in_progress }} active</span>
                  <span class="flex items-center gap-1.5" v-if="dashboards[project.name].data.stats.overdue"><span class="size-2 rounded-full bg-ink-red-5" /> {{ dashboards[project.name].data.stats.overdue }} overdue</span>
                </div>
              </div>

              <div class="flex flex-wrap gap-1.5 mb-3" v-if="dashboards[project.name]?.data?.phases?.length">
                <span v-for="phase in dashboards[project.name].data.phases.slice(0, 4)" :key="phase.name" class="text-xs px-2 py-0.5 rounded-full bg-surface-gray-1 text-ink-gray-6 border border-outline-gray-2">{{ phase.phase_name }} {{ phase.completed_count }}/{{ phase.total_count }}</span>
                <span v-if="dashboards[project.name].data.phases.length > 4" class="text-xs text-ink-gray-4 py-0.5">+{{ dashboards[project.name].data.phases.length - 4 }} more</span>
              </div>

              <div class="flex border border-outline-gray-2 rounded-lg overflow-hidden">
                <button class="flex-1 flex items-center justify-center gap-1.5 py-2 text-xs text-ink-gray-6 hover:bg-surface-gray-1 transition-colors" @click.stop="navigateToProject(project.name)"><FolderKanban class="size-3.5" /> Open</button>
                <button class="flex-1 flex items-center justify-center gap-1.5 py-2 text-xs text-ink-gray-6 hover:bg-surface-gray-1 transition-colors border-x border-outline-gray-2" @click.stop="onGenerateChecklist(project)"><ClipboardList class="size-3.5" /> Checklist</button>
                <button class="flex-1 flex items-center justify-center gap-1.5 py-2 text-xs text-ink-gray-6 hover:bg-surface-gray-1 transition-colors" @click.stop="navigateToKanban(project.name)"><Layout class="size-3.5" /> Board</button>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
    <GenerateChecklistModal
      v-if="showChecklistModal"
      :show="showChecklistModal"
      :project-id="selectedProjectId"
      @close="showChecklistModal = false"
      @generated="showChecklistModal = false; projects.reload()"
    />
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { createResource } from "frappe-ui";
import { __ } from "@/translation";
import LayoutHeader from "@/components/LayoutHeader.vue";
import GenerateChecklistModal from "./components/GenerateChecklistModal.vue";
import Plus from "~icons/lucide/plus";
import FolderKanban from "~icons/lucide/folder-kanban";
import AlertTriangle from "~icons/lucide/alert-triangle";
import ClipboardList from "~icons/lucide/clipboard-list";
import Layout from "~icons/lucide/layout";
import LucideX from "~icons/lucide/x";
import LucidePlus from "~icons/lucide/plus";
import LucideChevronUp from "~icons/lucide/chevron-up";
import LucideChevronDown from "~icons/lucide/chevron-down";

const router = useRouter();

interface Project {
  name: string;
  project_name?: string;
  title?: string;
  status?: string;
  expected_start_date?: string;
  expected_end_date?: string;
  priority?: string;
  start_date?: string;
}

const projects = createResource({
  url: "helpdesk.tasky.api.get_projects",
  auto: true,
  transform: (d: any[]) => d ?? [],
});

const userList = createResource({
  url: "helpdesk.tasky.api.get_users",
  auto: true,
  transform: (d: any[]) => d ?? [],
});

const createProject = createResource({
  url: "helpdesk.tasky.api.create_project",
  onSuccess() {
    showNewForm.value = false;
    resetForm();
    projects.reload();
  },
});


const showNewForm = ref(false);
const showChecklistModal = ref(false);
const selectedProjectId = ref("");
const expandedCards = reactive<Set<string>>(new Set());

function toggleExpand(name: string) {
  if (expandedCards.has(name)) expandedCards.delete(name);
  else expandedCards.add(name);
}

const newProject = reactive({
  project_name: "",
  start_date: "",
  expected_end_date: "",
  members: [] as { user: string; custom_role: string }[],
});

function resetForm() {
  newProject.project_name = "";
  newProject.start_date = "";
  newProject.expected_end_date = "";
  newProject.members = [];
}

function onCreateProject() {
  if (!newProject.project_name) return;
  createProject.submit({
    project_name: newProject.project_name,
    expected_start_date: newProject.start_date,
    expected_end_date: newProject.expected_end_date,
    members: JSON.stringify(newProject.members.filter((m) => m.user.trim())),
  });
}

function navigateToProject(projectName: string) {
  router.push({ name: "TaskyProject", params: { projectId: projectName } });
}

function navigateToKanban(projectName: string) {
  router.push({ name: "TaskyKanban", params: { projectId: projectName } });
}

const dashboards = reactive<Record<string, ReturnType<typeof createResource>>>({});

watch(
  () => projects.data,
  (list) => {
    list?.forEach((p) => {
      if (!dashboards[p.name]) {
        dashboards[p.name] = createResource({
          url: "helpdesk.tasky.api.get_project_dashboard",
          params: { project: p.name },
          auto: true,
        });
      }
    });
  },
  { immediate: true }
);

function formatDateRange(p: Project) {
  const parts = [];
  if (p.expected_start_date) parts.push(p.expected_start_date);
  if (p.expected_end_date) parts.push("→ " + p.expected_end_date);
  return parts.join(" ") || "No dates set";
}

function segments(project: Project) {
  const s = dashboards[project.name]?.data?.stats;
  const total = s?.total || 1;
  return {
    completed_pct: ((s?.completed || 0) / total * 100),
    working_pct: ((s?.in_progress || 0) / total * 100),
    review_pct: ((s?.reviewing || 0) / total * 100),
    cancelled_pct: ((s?.cancelled || 0) / total * 100),
    rest_pct: Math.max(0, 100 - (((s?.completed || 0) + (s?.in_progress || 0) + (s?.reviewing || 0) + (s?.cancelled || 0)) / total * 100)),
  };
}

function statusBadgeClass(status: string) {
  const m: Record<string, string> = {
    Open: "bg-ink-blue-1 text-ink-blue-8",
    Completed: "bg-ink-green-1 text-ink-green-8",
    Cancelled: "bg-ink-red-1 text-ink-red-8",
  };
  return m[status] || "bg-ink-gray-2 text-ink-gray-7";
}

function onGenerateChecklist(project: Project) {
  selectedProjectId.value = project.name;
  showChecklistModal.value = true;
}
</script>
