<template>
  <div
    class="activity flex cursor-pointer gap-3 rounded p-2.5 duration-300 ease-in-out hover:bg-surface-gray-1"
    @click="showModal = true"
  >
    <div class="flex flex-1 flex-col gap-1.5 truncate">
      <div class="font-medium text-ink-gray-9 truncate">
        {{ activity.title }}
      </div>

      <div class="flex flex-wrap items-center gap-1.5 text-sm text-ink-gray-6">
        <template v-if="activity.assigned_to">
          <div
            class="flex items-center gap-1.5 text-sm font-medium text-ink-gray-8"
          >
            <Avatar
              class="!h-4 !w-4 border border-outline-gray-2"
              shape="circle"
              :label="getAvatarLabel(activity.assigned_to)"
            />
            <span class="truncate max-w-[120px]">
              {{ getDisplayName(activity.assigned_to) }}
            </span>
          </div>
        </template>

        <template v-if="activity.due_date">
          <div
            v-if="activity.assigned_to"
            class="h-1 w-1 rounded-full bg-gray-400 mx-0.5"
          />

          <div class="flex items-center gap-1 text-ink-gray-5">
            <FeatherIcon name="calendar" class="h-3.5 w-3.5" />
            <span>
              {{ dateFormat(activity.due_date, "D MMM") }}
            </span>
          </div>
        </template>
      </div>
    </div>

    <div class="flex items-center gap-1" @click.stop>
      <Dropdown :options="statusOptions">
        <Button variant="ghost" class="hover:bg-surface-gray-3">
          <TaskStatusIcon :status="activity.status" />
        </Button>
      </Dropdown>

      <Dropdown :options="dropdownOptions" placement="right">
        <Button icon="more-horizontal" variant="ghost" />
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
import { Button, Dropdown, FeatherIcon, Avatar, call, toast } from "frappe-ui";
import { __ } from "@/translation";
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

// Clean up display names from emails (e.g., administrator@site.com -> Administrator)
function getDisplayName(email: string) {
  if (!email) return "";
  const namePart = email.split("@")[0];
  return namePart.charAt(0).toUpperCase() + namePart.slice(1);
}

// Convert user IDs to safe avatar initials fallback strings
function getAvatarLabel(email: string) {
  if (!email) return "";
  return getDisplayName(email);
}

function handleReload() {
  emit("update");
  if (props.reloadTasks) {
    props.reloadTasks();
  }
  showModal.value = false;
}

function stripHtml(html: string) {
  const div = document.createElement("div");
  div.innerHTML = html;
  return div.textContent || div.innerText || "";
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
  { label: __("Backlog"), onClick: () => changeStatus("Backlog") },
  { label: __("Todo"), onClick: () => changeStatus("Todo") },
  { label: __("In Progress"), onClick: () => changeStatus("In Progress") },
  { label: __("Done"), onClick: () => changeStatus("Done") },
  { label: __("Canceled"), onClick: () => changeStatus("Canceled") },
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
