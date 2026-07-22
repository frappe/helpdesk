<template>
  <div
    class="flex flex-col rounded-md px-2 py-4 grow w-full h-full overflow-hidden"
  >
    <div class="flex items-center gap-2 px-2 text-lg-semibold text-ink-gray-8">
      {{ __("Recent Activity") }}
      <Tooltip
        :text="__('Tickets you\'ve recently worked on or viewed')"
        placement="top"
      >
        <LucideInfo class="size-3.5 cursor-pointer text-ink-gray-5" />
      </Tooltip>
    </div>
    <div class="relative mt-5 grow overflow-hidden">
      <div class="flex flex-col h-full overflow-auto hide-scrollbar">
        <template v-if="!showSkeleton && activities.length > 0">
          <div
            v-for="activity in activities"
            :key="activity.name"
            @click="goToTicket(activity)"
            class="flex items-center gap-3 px-2 py-3 text-sm cursor-pointer hover:bg-surface-sidebar rounded"
          >
            <component
              :is="iconFor(activity.activity_type)"
              class="size-4 flex-shrink-0 text-ink-gray-5"
            />
            <div class="flex flex-col min-w-0 grow gap-1">
              <span class="truncate text-ink-gray-8">
                {{ activity.subject || __("Untitled") }}
              </span>
              <span class="truncate text-ink-gray-5">
                #{{ activity.name }} · {{ label(activity) }}
              </span>
            </div>
            <span class="text-ink-gray-4 whitespace-nowrap tabular-nums">
              {{ activity.timestamp }}
            </span>
          </div>
        </template>
        <div v-else class="flex flex-col">
          <div v-for="i in 6" :key="i" class="flex items-center gap-3 p-2 py-3">
            <div class="size-4 rounded-sm bg-surface-gray-1 flex-shrink-0" />
            <div class="flex flex-col gap-1 grow">
              <div class="h-4 w-2/3 rounded-sm bg-surface-gray-1" />
              <div class="h-3 w-1/3 rounded-sm bg-surface-gray-1" />
            </div>
          </div>
        </div>
      </div>
      <EmptyState
        v-if="!showSkeleton && activities.length === 0"
        class="absolute inset-0 z-10"
        :title="__('No recent activity')"
        :description="__('Tickets you act on will show up here')"
        variant="overlay"
        text="md"
      />
      <div
        v-if="!showSkeleton && activities.length > 0"
        class="pointer-events-none absolute inset-x-0 bottom-0 h-8"
        :style="{
          backgroundImage:
            'linear-gradient(to top, var(--surface-base), transparent)',
        }"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import EmptyState from "@/components/EmptyState.vue";
import { __ } from "@/translation";
import { createResource, Tooltip } from "frappe-ui";
import { computed, onMounted, ref, type PropType } from "vue";
import { useRouter } from "vue-router";
import ActivityIcon from "~icons/lucide/activity";
import ReplyIcon from "~icons/lucide/corner-up-left";
import EyeIcon from "~icons/lucide/eye";
import MessageSquareIcon from "~icons/lucide/message-square";

interface RecentActivity {
  name: string;
  subject: string;
  activity_type: "replied" | "commented" | "status" | "viewed";
  text: string | null;
  timestamp: string;
  creation: string;
}

const props = defineProps({
  data: {
    type: Array as PropType<RecentActivity[]>,
    required: true,
  },
});

const router = useRouter();

const typeLabels: Record<string, string> = {
  replied: __("Replied"),
  commented: __("Commented"),
  viewed: __("Viewed"),
};

const icons = {
  replied: ReplyIcon,
  commented: MessageSquareIcon,
  status: ActivityIcon,
  viewed: EyeIcon,
};

const hasLoadedOnce = ref(false);

const recentActivityResource = createResource({
  url: "helpdesk.api.agent_home.agent_home.get_recent_activity",
  onSuccess() {
    hasLoadedOnce.value = true;
  },
});

const activities = computed<RecentActivity[]>(() =>
  recentActivityResource.fetched ? recentActivityResource.data : props.data
);

const showSkeleton = computed(
  () => recentActivityResource.loading && !hasLoadedOnce.value
);

function iconFor(type: string) {
  return icons[type as keyof typeof icons] || ActivityIcon;
}

function label(activity: RecentActivity) {
  return activity.activity_type === "status"
    ? activity.text
    : typeLabels[activity.activity_type];
}

const goToTicket = (activity: RecentActivity) => {
  router.push({
    name: "TicketAgent",
    params: { ticketId: String(activity.name) },
  });
};

onMounted(() => {
  if (!Array.isArray(props.data)) {
    recentActivityResource.fetch();
  }
});
</script>
