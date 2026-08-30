<template>
  <div class="w-full">
    <hr v-if="i > 0" class="mx-4 border-0 border-t border-gray-200" />

    <div
      class="activity flex cursor-pointer items-start justify-between gap-4 px-4 py-3 rounded-xl hover:bg-surface-gray-1 transition-colors duration-200 w-full"
      @click="showModal = true"
    >
      <div class="flex flex-1 flex-col gap-2 min-w-0">
        <div class="truncate text-sm font-medium text-ink-gray-9">
          {{ localActivity.title || __("Untitled Task") }}
        </div>

        <div
          class="flex flex-wrap items-center gap-1.5 text-[13px] text-[#383838]"
        >
          <div v-if="assignedId" class="flex items-center gap-1.5">
            <Avatar
              shape="circle"
              size="xs"
              :label="userInfo.full_name || assigneeLabel"
              :image="userInfo.user_image || ''"
            />
            <span>{{ userInfo.full_name || assigneeLabel }}</span>
          </div>

          <div
            v-if="assignedId && localActivity.due_date"
            class="flex items-center justify-center"
          >
            <DotIcon class="h-1.5 w-1.5 text-ink-gray-4" />
          </div>

          <Tooltip
            v-if="localActivity.due_date"
            :text="dateFormat(localActivity.due_date, dateTooltipFormat)"
          >
            <div class="flex items-center gap-1.5">
              <CalendarIcon class="h-3.5 w-3.5 text-ink-gray-5" />
              <span>{{
                dateFormat(localActivity.due_date, "D MMM, h:mm A")
              }}</span>
            </div>
          </Tooltip>

          <div
            v-if="
              (assignedId || localActivity.due_date) && localActivity.priority
            "
            class="flex items-center justify-center"
          >
            <DotIcon class="h-1.5 w-1.5 text-ink-gray-4" />
          </div>

          <div v-if="localActivity.priority" class="flex items-center">
            <span>{{ localActivity.priority }}</span>
          </div>
        </div>
      </div>

      <div class="flex items-center gap-1 shrink-0" @click.stop>
        <Dropdown :options="statusDropdownOptions" placement="bottom-end">
          <Button
            :tooltip="__('Change Status')"
            variant="ghost"
            class="text-ink-gray-8 hover:bg-surface-gray-3 hover:text-ink-gray-9"
            :disabled="isUpdating"
          >
            <TaskStatusIcon
              :status="localActivity.status || 'Todo'"
              class="h-4 w-4"
            />
          </Button>
        </Dropdown>

        <Dropdown :options="actionMenuOptions" placement="bottom-end">
          <Button
            variant="ghost"
            icon="more-horizontal"
            class="text-ink-gray-8 hover:bg-surface-gray-3 hover:text-ink-gray-9"
            @click="isConfirmingDelete = false"
          />
        </Dropdown>
      </div>
    </div>

    <TaskboxEditor
      v-if="showModal"
      v-model="showModal"
      :task="localActivity"
      :ticketId="String(localActivity.reference_docname || '')"
      @submit="handleReload"
      @submit:load="load"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, nextTick } from "vue";
import { Avatar, Button, Dropdown, Tooltip, call, toast } from "frappe-ui";
import { dateTooltipFormat, dateFormat } from "@/utils";
import { __ } from "@/translation";
import { useUserStore } from "@/stores/user";
import CalendarIcon from "@/components/icons/CalendarIcon.vue";
import DotIcon from "@/components/icons/DotIcon.vue";
import TaskStatusIcon from "@/components/icons/TaskStatusIcon.vue";
import TaskboxEditor from "./TaskboxEditor.vue";

// --- Props & Emits ---
const props = defineProps({
  activity: {
    type: Object,
    required: true,
  },
  reloadTasks: {
    type: Function,
    default: null,
  },
  i: {
    type: Number,
    default: 0,
  },
  tasks: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits(["update", "status-change", "deleted"]);

// --- Reactivity State Layout ---
const showModal = ref(false);
const isUpdating = ref(false);
const isConfirmingDelete = ref(false);
const { getUser } = useUserStore();

const localActivity = ref({ ...props.activity });

// Keep local state synchronized if parent data fetches refresh
watch(
  () => props.activity,
  (newVal) => {
    if (newVal) {
      localActivity.value = { ...newVal };
    }
  },
  { deep: true }
);

// --- Normalization Mechanics ---
function normalizeAssignee(val: any): string {
  if (!val) return "";

  if (Array.isArray(val)) {
    return val[0] || "";
  }

  if (typeof val === "string") {
    const trimmed = val.trim();
    if (trimmed.startsWith("[")) {
      try {
        const arr = JSON.parse(trimmed);
        return Array.isArray(arr) ? arr[0] || "" : trimmed;
      } catch {
        return trimmed;
      }
    }
    return trimmed;
  }

  return String(val);
}

const assignedId = computed(() =>
  normalizeAssignee(
    localActivity.value.assigned || localActivity.value.assigned_to
  )
);

const userInfo = computed(() => {
  const email = assignedId.value;
  if (!email) return { full_name: "", user_image: "" };
  return getUser(email) || { full_name: "", user_image: "" };
});

const assigneeLabel = computed((): string => {
  return assignedId.value || "";
});

// --- Remote DB Async Callouts ---
async function changeStatus(newStatus: string) {
  if (isUpdating.value) return;

  const taskId = localActivity.value.name || localActivity.value.id;
  if (!taskId) {
    toast.error(__("Could not resolve Task ID."));
    return;
  }

  isUpdating.value = true;
  const previousStatus = localActivity.value.status;

  // Reactively replace the local object reference immediately
  localActivity.value = {
    ...localActivity.value,
    status: newStatus,
  };

  try {
    await call("helpdesk.helpdesk.doctype.hd_task.hd_task.update_task", {
      task: taskId,
      status: newStatus,
    });

    emit("status-change", { name: taskId, status: newStatus });
    emit("update", { ...localActivity.value, _refresh: Date.now() });

    await nextTick();
    if (props.reloadTasks) props.reloadTasks();
  } catch (e: any) {
    localActivity.value = {
      ...localActivity.value,
      status: previousStatus,
    };
    toast.error(e?.message || __("Failed to update status"));
  } finally {
    isUpdating.value = false;
  }
}

async function deleteTask() {
  if (isUpdating.value) return;

  const taskId = localActivity.value.name || localActivity.value.id;
  if (!taskId) {
    toast.error(__("Task identifier missing, cannot delete."));
    return;
  }

  isUpdating.value = true;
  emit("deleted", taskId);

  try {
    await call("helpdesk.helpdesk.doctype.hd_task.hd_task.delete_task", {
      task: taskId,
    });
    toast.success(__("Task deleted successfully"));
    emit("update", { deletedId: taskId, _refresh: Date.now() });

    await nextTick();
    if (props.reloadTasks) props.reloadTasks();
  } catch (e: any) {
    emit("update");
    toast.error(e?.message || __("Failed to delete task"));
  } finally {
    isUpdating.value = false;
    isConfirmingDelete.value = false;
  }
}

// --- Dropdown Options Config ---
const statusDropdownOptions = computed(() =>
  [
    { label: __("Backlog"), value: "Backlog" },
    { label: __("Todo"), value: "Todo" },
    { label: __("In Progress"), value: "In Progress" },
    { label: __("Done"), value: "Done" },
    { label: __("Canceled"), value: "Canceled" },
  ].map((s) => ({
    label: s.label,
    value: s.value,
    onClick: () => changeStatus(s.value),
  }))
);

const actionMenuOptions = computed(() => [
  {
    label: isConfirmingDelete.value ? __("Confirm Delete") : __("Delete"),
    icon: "trash-2",
    class: isConfirmingDelete.value
      ? "text-red-600 [&_svg]:text-red-600 font-medium bg-red-50 hover:bg-red-100 hover:text-red-600"
      : "text-ink-gray-7 hover:bg-surface-gray-1",
    onClick: (e: MouseEvent) => {
      if (!isConfirmingDelete.value) {
        e.preventDefault();
        e.stopPropagation();
        isConfirmingDelete.value = true;
      } else {
        deleteTask();
      }
    },
  },
]);

function processTaskUpdate(payload?: any) {
  showModal.value = false;
  const data = payload?.message || payload;

  if (data && typeof data === "object") {
    // Structure adjustments for assignee
    const rawAssignee = data.assigned ?? data.assigned_to;
    let normalizedAssignee = undefined;
    if (rawAssignee !== undefined) {
      normalizedAssignee = normalizeAssignee(rawAssignee);
    }

    // Force Vue tracking engine to trigger via spreading into a brand new object instance
    localActivity.value = {
      ...localActivity.value,
      ...data,
      ...(rawAssignee !== undefined && {
        assigned: normalizedAssignee,
        assigned_to: normalizedAssignee,
      }),
    };
  }
}

async function handleReload(payload?: any) {
  processTaskUpdate(payload);

  emit("update", {
    ...localActivity.value,
    _refresh: Date.now(),
  });

  await nextTick();

  if (props.reloadTasks) {
    props.reloadTasks();
  }
}

function load(payload?: any) {
  processTaskUpdate(payload);
}

// Initialization Triggers
emit("update", { ...localActivity.value });

if (props.reloadTasks) {
  props.reloadTasks();
}
</script>
