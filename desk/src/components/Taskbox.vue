<template>
  <div class="px-6 w-full">
    <div
      class="activity flex cursor-pointer items-start justify-between gap-4 py-3 hover:bg-surface-gray-1 duration-300 ease-in-out"
      @click="showModal = true"
    >
      <div class="flex flex-1 flex-col">

        <div class="truncate text-[15px] font-medium text-ink-gray-9">
          {{ activity.title || __('Untitled Task') }}
        </div>

        <div
          class="mt-1 flex flex-wrap items-center gap-2 text-[13px] text-ink-gray-600"
        >

          <div
            v-if="activity.assigned"
            class="flex items-center gap-1.5"
          >
            <Avatar
              shape="circle"
              :label="assigneeInfo.full_name || assigneeLabel"
              :image="assigneeInfo.user_image || ''"
              size="sm"
            />
            <span>
              {{ assigneeInfo.full_name || assigneeLabel }}
            </span>
          </div>

          <span
            v-if="activity.assigned && (activity.due_date || activity.priority)"
            class="text-gray-400"
          >
            &middot;
          </span>

          <div
            v-if="activity.due_date"
            class="flex items-center gap-1.5"
          >
            <Tooltip :text="dateFormat(activity.due_date)">
              <div class="flex items-center gap-1.5">
                <FeatherIcon
                  name="calendar"
                  class="h-3.5 w-3.5 text-gray-500"
                />
                <span>
                  {{ dateFormat(activity.due_date) }}
                </span>
              </div>
            </Tooltip>
          </div>

          <span
            v-if="activity.due_date && activity.priority"
            class="text-gray-400"
          >
            &middot;
          </span>

          <div
            v-if="activity.priority"
            class="flex items-center"
          >
            <span>
              {{ activity.priority }}
            </span>
          </div>

        </div>
      </div>

      <div
        class="flex items-center gap-1"
        @click.stop
      >

        <Tooltip :text="activity.status">
          <Dropdown
            :options="statusDropdownOptions"
            placement="bottom-end"
          >
            <template #default>
              <Button
                variant="ghost"
                class="hover:bg-surface-gray-4"
                :disabled="isUpdating"
                @click.stop.prevent
              >
                <TaskStatusIcon :status="activity.status" />
              </Button>
            </template>

            <template #item="{ item }">
              <button
                class="flex w-full items-center gap-2.5 rounded px-2.5 py-1.5 text-sm text-ink-gray-9 hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                :disabled="isUpdating"
                @click="item.onClick"
              >
                <TaskStatusIcon :status="item.value" class="h-4 w-4 shrink-0" />
                <span class="whitespace-nowrap">{{ item.label }}</span>
              </button>
            </template>
          </Dropdown>
        </Tooltip>

        <Dropdown
          :options="dropdownOptions"
          placement="bottom-end"
        >
          <Button
            icon="more-horizontal"
            variant="ghost"
            @click.stop.prevent
          />
        </Dropdown>

      </div>
    </div>

    <div class="border-b border-gray-200 w-full" />

    <TaskboxEditor
      v-model="showModal"
      :task="activity"
      :ticketId="String(activity.reference_docname || '')"
      @submit="handleReload"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { Avatar, Button, Dropdown, FeatherIcon, Tooltip, call, toast } from "frappe-ui";
import { __ } from "@/translation";
import { useUserStore } from "@/stores/user";
import { dateFormat } from "@/utils";
import TaskStatusIcon from "@/components/icons/TaskStatusIcon.vue";
import TaskboxEditor from "./TaskboxEditor.vue";

const props = defineProps({
  activity: {
    type: Object,
    required: true,
  },
  reloadTasks: {
    type: Function,
    default: null,
  },
});

const emit = defineEmits(["update"]);
const showModal = ref(false);
const isUpdating = ref(false);

const { getUser } = useUserStore();

/* Assignee Info */
const assigneeInfo = computed(() => {
  const email = props.activity.assigned;
  if (!email) {
    return { full_name: "", user_image: "" };
  }
  return getUser(email) || { full_name: "", user_image: "" };
});

/* Assignee Label */
const assigneeLabel = computed((): string => {
  const assigned = props.activity.assigned;
  if (!assigned) return "";
  if (!assigned.includes("@")) {
    return assigned;
  }
  return assigned
    .split("@")[0]
    .split(/[._-]/)
    .map((word: string) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
});

/* Reload */
function handleReload() {
  showModal.value = false;
  emit("update");
  props.reloadTasks?.();
}

/* Change Status */
async function changeStatus(newStatus: string) {
  if (isUpdating.value) return;
  isUpdating.value = true;
  try {
    await call("helpdesk.helpdesk.doctype.hd_task.hd_task.update_task", {
      task: props.activity.name,
      status: newStatus,
    });
    handleReload();
  } catch (e: any) {
    toast.error(e?.message || __("Failed to update status"));
  } finally {
    isUpdating.value = false;
  }
}

/* Status Dropdown Options */
const statusDropdownOptions = computed(() => {
  const statuses = [
    { label: __("Backlog"), value: "Backlog" },
    { label: __("Todo"), value: "Todo" },
    { label: __("In Progress"), value: "In Progress" },
    { label: __("Done"), value: "Done" },
    { label: __("Canceled"), value: "Canceled" },
  ];
  return statuses.map((status) => ({
    label: status.label,
    value: status.value,
    onClick: () => changeStatus(status.value),
  }));
});

/* More Options */
const dropdownOptions = computed(() => [
  {
    label: __("Delete"),
    icon: "trash-2",
    onClick: async () => {
      try {
        await call("helpdesk.helpdesk.doctype.hd_task.hd_task.delete_task", {
          task: props.activity.name,
        });
        toast.success(__("Task deleted"));
        handleReload();
      } catch (e: any) {
        toast.error(e?.message || __("Failed to delete task"));
      }
    },
  },
]);
</script>