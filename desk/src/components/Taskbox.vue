<template>
  <div
    class="flex cursor-pointer items-center gap-3 rounded-md px-3 py-4 transition duration-150 ease-in-out hover:bg-surface-gray-1 group"
    @click="showModal = true"
  >
    <!-- Title + meta (takes all available width) -->
    <div class="flex flex-1 flex-col gap-1 min-w-0">

      <!-- Title -->
      <div class="truncate text-base font-semibold text-ink-gray-9">
        {{ activity.title || __("Untitled Task") }}
      </div>

      <!-- Meta row: avatar · name · date · priority -->
      <div class="flex flex-wrap items-center gap-1.5 text-sm text-ink-gray-8">

        <!-- Assignee with real profile photo -->
        <template v-if="activity.assigned">
          <div class="flex items-center gap-1">
            <Avatar
              class="!h-5 !w-5 flex-shrink-0"
              shape="circle"
              :label="assigneeInfo.full_name || assigneeLabel"
              :image="assigneeInfo.user_image || ''"
            />
            <span class="truncate max-w-[120px] text-ink-gray-5">
              {{ assigneeInfo.full_name || assigneeLabel }}
            </span>
          </div>
          <span class="text-ink-gray-5">&middot;</span>
        </template>

        <!-- Due date with calendar icon -->
        <template v-if="activity.due_date">
          <div class="flex items-center gap-1 text-ink-gray-8">
            <FeatherIcon name="calendar" class="h-3.5 w-3.5 flex-shrink-0" />
            <span>{{ formatDueDate(activity.due_date) }}</span>
          </div>
          <span v-if="activity.priority" class="text-ink-gray-5">&middot;</span>
        </template>

        <!-- Priority -->
        <template v-if="activity.priority">
          <span class="text-ink-gray-8 font-medium">{{ activity.priority }}</span>
        </template>

      </div>
    </div>

    <!-- Right: status picker + ··· menu -->
    <div class="flex flex-shrink-0 items-center gap-1" @click.stop>
      <Dropdown :options="statusOptions">
        <button
          class="flex items-center justify-center rounded-full p-0.5 hover:bg-surface-gray-2 focus:outline-none"
          :title="activity.status"
        >
          <TaskStatusIcon :status="activity.status" />
        </button>
      </Dropdown>

      <Dropdown :options="dropdownOptions" placement="right">
        <Button
          icon="more-horizontal"
          variant="ghost"
          class="h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity duration-150"
        />
      </Dropdown>
    </div>
  </div>

  <TaskboxEditor
    v-model="showModal"
    :task="activity"
    :ticketId="String(activity.reference_docname || '')"
    @submit="handleReload"
  />
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { Avatar, Button, Dropdown, FeatherIcon, call, toast } from "frappe-ui";
import { __ } from "@/translation";
import { useUserStore } from "@/stores/user";
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

const { getUser } = useUserStore();


const assigneeInfo = computed(() => {
  const email = props.activity.assigned;
  if (!email) return { full_name: "", user_image: "" };
  return getUser(email) || { full_name: "", user_image: "" };
});


const assigneeLabel = computed((): string => {
  const a = props.activity.assigned;
  if (!a) return "";
  if (!a.includes("@")) return a;
  return a.split("@")[0]
    .split(/[._-]/)
    .map((w: string) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
});

function formatDueDate(dateStr: string): string {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return dateStr;
  // toLocaleString (not toLocaleDateString) is required to render time
  return d.toLocaleString("en-GB", {
    day:    "numeric",
    month:  "short",
    hour:   "2-digit",
    minute: "2-digit",
    hour12: true,
  });
}
function handleReload() {
  showModal.value = false;
  emit("update");
  props.reloadTasks?.();
}
async function changeStatus(newStatus: string) {
  try {
    await call("helpdesk.helpdesk.doctype.hd_task.hd_task.update_task", {
      task:   props.activity.name,
      status: newStatus,
    });
    handleReload();
  } catch (e: any) {
    toast.error(e?.message || __("Failed to update status"));
  }
}

const statusOptions = computed(() => [
  { label: __("Backlog"),     onClick: () => changeStatus("Backlog") },
  { label: __("Todo"),        onClick: () => changeStatus("Todo") },
  { label: __("In Progress"), onClick: () => changeStatus("In Progress") },
  { label: __("Done"),        onClick: () => changeStatus("Done") },
  { label: __("Canceled"),    onClick: () => changeStatus("Canceled") },
]);
const dropdownOptions = computed(() => [
  {
    label:   __("Delete"),
    icon:    "trash-2",
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