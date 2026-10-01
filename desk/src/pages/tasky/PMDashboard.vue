<template>
  <div class="flex flex-col h-full">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg-medium text-ink-gray-9">
          {{ projectDetail.data?.project_name || __("Project Dashboard") }}
        </div>
      </template>
      <template #right-header>
        <div class="flex items-center gap-1">
          <router-link
            v-for="tab in tabs"
            :key="tab.to"
            :to="{ name: tab.to, params: { projectId } }"
            class="px-3 py-1.5 rounded text-sm transition-colors"
            :class="isActiveTab(tab.to)
              ? 'bg-surface-gray-3 text-ink-gray-9'
              : 'text-ink-gray-6 hover:bg-surface-gray-2 hover:text-ink-gray-8'"
          >
            {{ __(tab.label) }}
          </router-link>
        </div>
      </template>
    </LayoutHeader>

    <div class="flex-1 overflow-auto p-5">
      <div
        v-if="!projectId"
        class="flex items-center justify-center h-full"
      >
        <div class="flex flex-col items-center gap-2">
          <GanttChartSquare class="size-12 text-ink-gray-4" />
          <div class="text-lg-medium text-ink-gray-8">
            {{ __("No project selected") }}
          </div>
          <div class="text-p-base text-ink-gray-6">
            {{ __("Select a project to view its dashboard.") }}
          </div>
        </div>
      </div>

      <div
        v-else-if="dashboard.loading || projectDetail.loading"
        class="flex items-center justify-center h-full"
      >
        <div class="text-p-base text-ink-gray-6">{{ __("Loading...") }}</div>
      </div>

      <div
        v-else-if="dashboard.error || projectDetail.error"
        class="flex items-center justify-center h-full"
      >
        <div class="flex flex-col items-center gap-2">
          <AlertTriangle class="size-10 text-ink-gray-5" />
          <div class="text-p-base text-ink-gray-7">
            {{
              __(
                "Failed to load dashboard data. Please try again."
              )
            }}
          </div>
        </div>
      </div>

      <template v-else>
        <div class="mb-6">
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm-medium text-ink-gray-7">
              {{ __("Overall Progress") }}
            </span>
            <span class="text-sm-medium text-ink-gray-9">
              {{ progressPercent }}%
            </span>
          </div>
          <div class="w-full h-3 rounded-full bg-surface-gray-2 overflow-hidden">
            <div
              class="h-full rounded-full bg-surface-gray-6 transition-all duration-500"
              :style="{ width: progressPercent + '%' }"
            />
          </div>
        </div>

        <div class="grid grid-cols-3 gap-4 mb-6">
          <div
            v-for="card in statCards"
            :key="card.label"
            class="bg-surface-white border border-outline-gray-2 rounded-lg p-4"
          >
            <div class="flex items-center gap-2 mb-2">
              <component :is="card.icon" :class="card.iconClasses || 'text-ink-gray-5'" class="size-4" />
              <span class="text-xs" :class="card.classes || 'text-ink-gray-6'">{{ __(card.label) }}</span>
            </div>
            <div class="text-xl-semibold" :class="card.classes || 'text-ink-gray-9'">
              {{ card.value }}
            </div>
          </div>
        </div>

        <div class="mb-6">
          <div class="text-sm-medium text-ink-gray-7 mb-3">
            {{ __("Phases") }}
          </div>
          <div class="bg-surface-white border border-outline-gray-2 rounded-lg">
            <div
              v-if="phases.length === 0"
              class="p-4 text-center text-p-sm text-ink-gray-5"
            >
              {{ __("No phases yet") }}
            </div>
            <div
              v-for="(phase, index) in phases"
              :key="phase.name"
              class="flex items-center gap-4 p-3"
              :class="{
                'border-b border-outline-gray-2': index < phases.length - 1,
              }"
            >
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-1">
                  <span class="text-sm text-ink-gray-8 truncate">
                    {{ phase.phase_name }}
                  </span>
                </div>
                <div class="flex items-center gap-2 text-xs text-ink-gray-6 mb-1">
                  <span>{{ phase.completed_count }} / {{ phase.total_count }} {{ __("tasks") }}</span>
                </div>
                <div class="w-full h-2 rounded-full bg-surface-gray-2 overflow-hidden">
                  <div
                    class="h-full rounded-full bg-surface-gray-5 transition-all duration-500"
                    :style="{ width: phase.progress_pct + '%' }"
                  />
                </div>
              </div>
              <span class="text-xs text-ink-gray-6 w-10 text-right">
                {{ phase.progress_pct }}%
              </span>
            </div>
          </div>
        </div>

        <div>
          <div class="text-sm-medium text-ink-gray-7 mb-3">
            {{ __("Team Workload") }}
          </div>
          <div class="bg-surface-white border border-outline-gray-2 rounded-lg">
            <div
              v-if="teamWorkload.length === 0"
              class="p-4 text-center text-p-sm text-ink-gray-5"
            >
              {{ __("No team members yet") }}
            </div>
            <div
              v-for="(member, index) in teamWorkload"
              :key="member.user"
              class="flex items-center gap-3 p-3"
              :class="{
                'border-b border-outline-gray-2': index < teamWorkload.length - 1,
              }"
            >
              <div class="flex-1 min-w-0">
                <div class="text-sm text-ink-gray-8 truncate">
                  {{ member.full_name || member.user }}
                </div>
              </div>
            </div>
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
import CheckCircle2 from "~icons/lucide/check-circle-2";
import AlertTriangle from "~icons/lucide/alert-triangle";
import Clock from "~icons/lucide/clock";
import GanttChartSquare from "~icons/lucide/gantt-chart-square";
import ListTodo from "~icons/lucide/list-todo";
import ListChecks from "~icons/lucide/list-checks";

const props = defineProps<{
  projectId?: string;
}>();

const route = useRoute();

const tabs = [
  { label: "Dashboard", to: "TaskyProject" },
  { label: "Checklist", to: "TaskyChecklist" },
  { label: "Board", to: "TaskyKanban" },
  { label: "Timeline", to: "TaskyTimeline" },
  { label: "Overdue", to: "TaskyOverdue" },
];

function isActiveTab(name: string) {
  return route.name === name;
}

const dashboard = createResource({
  url: "helpdesk.tasky.api.get_project_dashboard",
  makeParams: () => ({ project: props.projectId }),
});

const projectDetail = createResource({
  url: "helpdesk.tasky.api.get_project_detail",
  makeParams: () => ({ project: props.projectId }),
});

watch(
  () => props.projectId,
  (val) => {
    if (val) {
      dashboard.reload();
      projectDetail.reload();
    }
  },
  { immediate: true }
);

interface PhaseItem {
  name: string;
  phase_name: string;
  total_count: number;
  completed_count: number;
  progress_pct: number;
}

interface TeamMember {
  user: string;
  full_name: string;
}

const progressPercent = computed(() => {
  if (dashboard.data?.stats?.completion_pct != null) {
    return dashboard.data.stats.completion_pct;
  }
  return projectDetail.data?.progress ?? 0;
});

const statCards = computed(() => {
  const stats = dashboard.data?.stats ?? {};
  return [
    {
      label: "Total Tasks",
      icon: ListTodo,
      value: stats.total ?? 0,
    },
    {
      label: "Completed",
      icon: CheckCircle2,
      value: stats.completed ?? 0,
    },
    {
      label: "In Progress",
      icon: Clock,
      value: stats.in_progress ?? 0,
    },
    {
      label: "Blocked",
      icon: AlertTriangle,
      value: stats.blocked ?? 0,
    },
    {
      label: "Overdue",
      icon: AlertTriangle,
      value: stats.overdue ?? 0,
      classes: "text-ink-red-7",
      iconClasses: "text-ink-red-5",
    },
    {
      label: "Completion %",
      icon: ListChecks,
      value: stats.completion_pct != null ? `${stats.completion_pct}%` : "0%",
    },
  ];
});

const phases = computed<PhaseItem[]>(() => {
  return dashboard.data?.phases ?? [];
});

const teamWorkload = computed<TeamMember[]>(() => {
  return projectDetail.data?.users ?? [];
});


</script>
