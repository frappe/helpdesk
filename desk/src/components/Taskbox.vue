<template>
  <div
    class="flex cursor-pointer items-center gap-3 rounded-md px-3 py-3.5 transition duration-150 ease-in-out hover:bg-surface-gray-1 group border-b border-gray-100 last:border-b-0"
    @click="showModal = true"
  >
    
    <div class="flex flex-1 flex-col gap-1 min-w-0">


      <div class="truncate text-base font-medium text-gray-900">
        {{ activity.title || __("Untitled Task") }}
      </div>

      <div class="flex flex-wrap items-center gap-2 text-sm text-gray-600">

        <template v-if="activity.assigned">
          <div class="flex items-center gap-1.5">
            <div class="flex items-center flex-shrink-0">
              <Avatar
                shape="circle"
                :label="assigneeInfo.full_name || assigneeLabel"
                :image="assigneeInfo.user_image || ''"
                size="sm"
              />
            </div>
            <span class="truncate max-w-[120px]">
              {{ assigneeInfo.full_name || assigneeLabel }}
            </span>
          </div>
        </template>

        <template v-if="activity.due_date">
          <div class="flex items-center gap-1">
            <FeatherIcon name="calendar" class="h-3.5 w-3.5 flex-shrink-0 text-gray-500" />
            <span>{{ dateFormat(activity.due_date) }}</span>
          </div>
        </template>

        <template v-if="activity.priority">
          <span>{{ activity.priority }}</span>
        </template>

      </div>
    </div>

    <div class="flex flex-shrink-0 items-center gap-1" @click.stop>

      <Tooltip :text="activity.status">
        <Dropdown :options="statusOptions">
          <button
            class="flex items-center justify-center rounded-full p-0.5 hover:bg-surface-gray-2 focus:outline-none"
          >
            <TaskStatusIcon :status="activity.status" class="[&_circle]:stroke-gray-700 [&_path]:stroke-gray-700" />
          </button>
        </Dropdown>
      </Tooltip>

      <Dropdown :options="dropdownOptions" placement="right">
        <Button
          icon="more-horizontal"
          variant="ghost"
          class="h-7 w-7"
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
import { Avatar, Button, Dropdown, FeatherIcon, Tooltip, call, toast } from "frappe-ui";
import { __ } from "@/translation";
import { useUserStore } from "@/stores/user";
import TaskStatusIcon from "@/components/icons/TaskStatusIcon.vue";
import TaskboxEditor from "./TaskboxEditor.vue";
import { dateFormat } from "@/utils";

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
  return a
    .split("@")[0]
    .split(/[._-]/)
    .map((w: string) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
});

function handleReload() {
  showModal.value = false;
  emit("update");
  props.reloadTasks?.();
}

async function changeStatus(newStatus: string) {
  try {
    await call("helpdesk.helpdesk.doctype.hd_task.hd_task.update_task", {
      task: props.activity.name,
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