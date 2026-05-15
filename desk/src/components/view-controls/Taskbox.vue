<template>
  <div
    class="border flex-1 px-4 py-3 mb-4 bg-white rounded-lg shadow-sm"
    ref="taskBoxRef"
  >
    <div class="flex items-start justify-between gap-4">
      <div class="flex gap-3 flex-1">
        <!-- Avatar -->
        <Avatar
          :label="getUser(activity.owner).full_name"
          :image="getUser(activity.owner).user_image"
          size="md"
        />

        <!-- Content -->
        <div class="flex-1">
          <!-- Header (always visible) -->
          <div class="flex items-center gap-2 flex-wrap">
            <div class="font-semibold text-gray-900 text-base">
              {{ localActivity.subject || localActivity.title }}
            </div>
            <div class="text-xs px-2 py-1 rounded-full" :class="statusClass">
              {{ localActivity.status }}
            </div>
          </div>

          <!-- ── EDIT MODE ── -->
          <div v-if="editable" class="mt-3 flex flex-col gap-3">
            <!-- Subject -->
            <FormControl
              v-model="editForm.subject"
              :label="__('Subject')"
              type="text"
              size="sm"
              variant="subtle"
              :placeholder="__('Enter task subject')"
            />

            <!-- Status + Priority -->
            <div class="grid grid-cols-2 gap-3">
              <FormControl
                v-model="editForm.status"
                :label="__('Status')"
                type="select"
                size="sm"
                variant="subtle"
                :options="statusOptions"
              />
              <FormControl
                v-model="editForm.priority"
                :label="__('Priority')"
                type="select"
                size="sm"
                variant="subtle"
                :options="priorityOptions"
              />
            </div>

            <!-- Start + End date -->
            <div class="grid grid-cols-2 gap-3">
              <FormControl
                v-model="editForm.expected_start_date"
                :label="__('Start Date')"
                type="date"
                size="sm"
                variant="subtle"
              />
              <FormControl
                v-model="editForm.expected_end_date"
                :label="__('End Date')"
                type="date"
                size="sm"
                variant="subtle"
              />
            </div>

            <!-- Description -->
            <div class="flex flex-col gap-1">
              <label class="block text-xs text-gray-600">
                {{ __("Description") }}
              </label>
              <TextEditor
                :editor-class="[
                  'prose-sm max-w-none min-h-[5rem] border rounded px-3 py-2',
                  getFontFamily(_description),
                ]"
                :content="_description"
                :editable="true"
                :starterkit-options="{ heading: { levels: [2, 3, 4, 5, 6] } }"
                :placeholder="__('Optional description')"
                @change="(v) => (_description = v)"
              />
            </div>

            <!-- Save / Discard -->
            <div class="flex justify-end gap-2">
              <Button :label="__('Discard')" @click="handleDiscard" />
              <Button
                variant="solid"
                :label="__('Save')"
                :loading="saving"
                :disabled="!editForm.subject?.trim() || saving"
                @click="handleSave"
              />
            </div>
          </div>

          <!-- ── VIEW MODE ── -->
          <div
            v-else-if="localActivity.task_description"
            class="text-sm text-gray-600 mt-2"
            v-html="localActivity.task_description"
          />

          <!-- Footer -->
          <div
            class="flex items-center gap-3 mt-3 text-xs text-gray-500 flex-wrap"
          >
            <Tooltip
              :text="dateFormat(localActivity.creation, dateTooltipFormat)"
            >
              <span>{{ timeAgo(localActivity.creation) }}</span>
            </Tooltip>
            <div class="px-2 py-1 rounded-full" :class="priorityClass">
              {{ localActivity.priority }}
            </div>
            <span v-if="localActivity.expected_start_date">
              Start: {{ localActivity.expected_start_date }}
            </span>
            <span v-if="localActivity.expected_end_date">
              Due: {{ localActivity.expected_end_date }}
            </span>
          </div>
        </div>
      </div>

      <!-- ── DROPDOWN (owner only, view mode only) ── -->
      <div v-if="authStore.userId === activity.owner && !editable">
        <Dropdown
          placement="right"
          :options="dropdownOptions"
          @click="isConfirmingDelete = false"
        >
          <Button
            icon="more-horizontal"
            class="text-gray-600"
            variant="ghost"
          />
        </Dropdown>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { useAuthStore } from "@/stores/auth";
import { useUserStore } from "@/stores/user";
import { __ } from "@/translation";

// ── exact same imports as CommentBox.vue ──────────────────────────────────────
import {
  ConfirmDelete,
  dateFormat,
  dateTooltipFormat,
  getFontFamily,
  isContentEmpty,
  timeAgo,
} from "@/utils";

import {
  Avatar,
  Button,
  Dropdown,
  FormControl,
  TextEditor,
  Tooltip,
  call,
  createResource,
  toast,
} from "frappe-ui";

// ── Props / Emits ─────────────────────────────────────────────────────────────

const props = defineProps({
  activity: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(["update"]);

const authStore = useAuthStore();
const { getUser } = useUserStore();

const taskBoxRef = ref(null);
const editable = ref(false);
const saving = ref(false);
const isConfirmingDelete = ref(false);

const _description = ref(props.activity.task_description);

const editFormSnapshot = ref(props.activity.task_description);

const lastSavedDescription = ref(props.activity.task_description);

const localActivity = ref({ ...props.activity });

// all editable fields (mirrors the full form, not just description)
const editForm = ref({
  subject: props.activity.subject || "",
  status: props.activity.status || "Open",
  priority: props.activity.priority || "Medium",
  expected_start_date: props.activity.expected_start_date || "",
  expected_end_date: props.activity.expected_end_date || "",
});

const statusOptions = [
  { label: __("Open"), value: "Open" },
  { label: __("Working"), value: "Working" },
  { label: __("Pending Review"), value: "Pending Review" },
  { label: __("Completed"), value: "Completed" },
  { label: __("Cancelled"), value: "Cancelled" },
];

const priorityOptions = [
  { label: __("Low"), value: "Low" },
  { label: __("Medium"), value: "Medium" },
  { label: __("High"), value: "High" },
  { label: __("Urgent"), value: "Urgent" },
];

const statusClass = computed(() => ({
  "bg-gray-100 text-gray-700": localActivity.value.status === "Open",
  "bg-blue-100 text-blue-700": localActivity.value.status === "Working",
  "bg-yellow-100 text-yellow-700":
    localActivity.value.status === "Pending Review",
  "bg-green-100 text-green-700": localActivity.value.status === "Completed",
  "bg-red-100 text-red-700":
    localActivity.value.status === "Cancelled" ||
    localActivity.value.status === "Overdue",
}));

const priorityClass = computed(() => ({
  "bg-green-100 text-green-700": localActivity.value.priority === "Low",
  "bg-yellow-100 text-yellow-700": localActivity.value.priority === "Medium",
  "bg-orange-100 text-orange-700": localActivity.value.priority === "High",
  "bg-red-100 text-red-700": localActivity.value.priority === "Urgent",
}));

const dropdownOptions = computed(() => [
  {
    label: __("Edit"),
    icon: "edit-2",
    onClick: () => handleEditMode(),
  },
  ...ConfirmDelete({
    onConfirmDelete: () => deleteTask.submit(),
    isConfirmingDelete,
  }),
]);

const deleteTask = createResource({
  url: "frappe.client.delete",
  makeParams: () => ({
    doctype: "HD Task",
    name: props.activity.name,
  }),
  onSuccess() {
    emit("update");
    toast.success(__("Task deleted successfully."));
  },
  onError(e: any) {
    toast.error(e?.message || __("Failed to delete task"));
  },
});

function handleEditMode() {
  // mirrors: commentBoxState.value = _content.value
  editFormSnapshot.value = _description.value;
  editForm.value = {
    subject: localActivity.value.subject || "",
    status: localActivity.value.status || "Open",
    priority: localActivity.value.priority || "Medium",
    expected_start_date: localActivity.value.expected_start_date || "",
    expected_end_date: localActivity.value.expected_end_date || "",
  };
  editable.value = true;
}

function handleDiscard() {
  // mirrors: _content.value = commentBoxState.value
  _description.value = editFormSnapshot.value;
  editable.value = false;
}

async function handleSave() {
  // mirrors: if (lastSavedContent.value === _content.value)
  const descriptionUnchanged =
    lastSavedDescription.value === _description.value;
  const fieldsUnchanged =
    editForm.value.subject === localActivity.value.subject &&
    editForm.value.status === localActivity.value.status &&
    editForm.value.priority === localActivity.value.priority &&
    editForm.value.expected_start_date ===
      localActivity.value.expected_start_date &&
    editForm.value.expected_end_date === localActivity.value.expected_end_date;

  if (descriptionUnchanged && fieldsUnchanged) {
    editable.value = false;
    return;
  }

  // mirrors: if (isContentEmpty(_content.value))
  if (!editForm.value.subject?.trim()) {
    toast.error(__("Subject is required"));
    return;
  }

  if (saving.value) return;
  saving.value = true;

  try {
    const response = await call(
      "helpdesk.helpdesk.doctype.hd_task.hd_task.update_task",
      {
        task: props.activity.name,
        subject: editForm.value.subject,
        status: editForm.value.status,
        priority: editForm.value.priority,
        task_description: isContentEmpty(_description.value)
          ? null
          : _description.value,
        expected_start_date: editForm.value.expected_start_date || null,
        expected_end_date: editForm.value.expected_end_date || null,
      }
    );

    // mirrors: lastSavedContent.value = _content.value
    lastSavedDescription.value = _description.value;
    localActivity.value = { ...localActivity.value, ...response };

    editable.value = false;
    emit("update");
    toast.success(__("Task updated successfully."));
  } catch (e: any) {
    toast.error(e?.message || __("Failed to update task"));
  } finally {
    saving.value = false;
  }
}

onMounted(() => {
  taskBoxRef.value.style.width = "0px";
});
</script>
