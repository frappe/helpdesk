<template>
  <Dialog v-model="show" :options="{ size: 'xl' }">
    <template #body-title>
      <div class="flex items-center justify-between w-full pr-8">
        <h3 class="text-xl font-semibold leading-6 text-ink-gray-9">
          {{ isEditing ? __("Edit Task") : __("Create Task") }}
        </h3>
      </div>
    </template>

    <template #body-content>
      <div class="flex flex-col gap-5 mt-2">
        <!-- Title Input -->
        <div class="space-y-1.5">
          <div class="flex items-center justify-between">
            <div class="text-sm text-ink-gray-5 flex items-center gap-1">
              {{ __("Title") }} <span class="text-red-500">*</span>
            </div>
            <span
              class="text-xs transition-colors"
              :class="
                form.title.length > 140
                  ? 'text-red-500 font-semibold'
                  : 'text-ink-gray-4'
              "
            >
              {{ form.title.length }}/140
            </span>
          </div>
          <TextInput
            ref="titleRef"
            v-model="form.title"
            variant="subtle"
            class="w-full rounded-md transition-all border"
            :class="{
              'border-red-500 ring-1 ring-red-500 focus:border-red-500 focus:ring-red-500':
                errors.title || errors.titleLength,
            }"
            :placeholder="__('Enter task title')"
          />
          <p v-if="errors.title" class="text-xs text-red-500 font-medium">
            {{ __("Title is required") }}
          </p>
          <p v-if="errors.titleLength" class="text-xs text-red-500 font-medium">
            {{ __("Title cannot exceed 140 characters") }}
          </p>
        </div>

        <!-- Description Editor -->
        <div class="space-y-1.5">
          <div class="flex items-center justify-between">
            <div class="text-sm text-ink-gray-5 flex items-center gap-1">
              {{ __("Description") }} <span class="text-red-500">*</span>
            </div>
            <span
              class="text-xs transition-colors"
              :class="
                getDescriptionLength > 4000
                  ? 'text-red-500 font-semibold'
                  : 'text-ink-gray-4'
              "
            >
              {{ getDescriptionLength }}/4000
            </span>
          </div>
          <CompactEditor
            v-model="form.description"
            :placeholder="__('Enter task description...')"
            :class="{
              'border-red-500 ring-1 ring-red-500':
                errors.description || errors.descriptionLength,
            }"
          />
          <p v-if="errors.description" class="text-xs text-red-500 font-medium">
            {{ __("Description is required") }}
          </p>
          <p
            v-if="errors.descriptionLength"
            class="text-xs text-red-500 font-medium"
          >
            {{ __("Description exceeds character limit (Max 4,000)") }}
          </p>
        </div>

        <!-- Metadata Properties Grid Layout -->
        <div class="grid grid-cols-2 gap-4">
          <!-- Priority Selector -->
          <div class="space-y-1.5">
            <div class="text-sm text-ink-gray-5">{{ __("Priority") }}</div>
            <div class="relative flex items-center">
              <TaskPriorityIcon
                :priority="form.priority"
                class="absolute left-3 z-10 h-4 w-4 pointer-events-none"
              />
              <FormControl
                type="select"
                variant="subtle"
                class="w-full !pl-9"
                :options="priorityOptions"
                v-model="form.priority"
              />
            </div>
          </div>

          <!-- Assignee Selector -->
          <div class="space-y-1.5">
            <div class="text-sm text-ink-gray-5">{{ __("Assigned To") }}</div>
            <Autocomplete
              :options="agentOptions"
              :value="form.assigned"
              @change="handleAssigneeChange"
              :placeholder="__('Assigned To')"
              class="w-full"
            >
              <template #target="{ togglePopover }">
                <Button
                  variant="subtle"
                  class="w-full flex items-center justify-between font-normal text-ink-gray-8"
                  @click="togglePopover"
                >
                  <div class="flex items-center gap-2 truncate">
                    <Avatar
                      v-if="form.assigned"
                      class="!h-4 !w-4 flex-shrink-0"
                      shape="circle"
                      :label="assigneeLabel"
                      :image="getAssigneeImage(form.assigned)"
                    />
                    <span class="truncate">{{
                      assigneeLabel || __("Assigned To")
                    }}</span>
                  </div>
                  <template #suffix>
                    <FeatherIcon
                      name="chevron-down"
                      class="h-4 w-4 text-ink-gray-5"
                    />
                  </template>
                </Button>
              </template>
              <template #item-prefix="{ option }">
                <Avatar
                  class="mr-2 !h-5 !w-5 flex-shrink-0"
                  shape="circle"
                  :label="option.label"
                  :image="option.image"
                />
              </template>
            </Autocomplete>
          </div>

          <!-- Due Date Selector -->
          <div class="space-y-1.5">
            <div class="text-sm text-ink-gray-5">{{ __("Due Date") }}</div>
            <div class="w-full date-picker-wrapper">
              <DateTimePicker
                v-model="form.due_date"
                :placeholder="__('Due Date')"
                format="DD-MM-YYYY HH:mm"
              />
            </div>
          </div>

          <!-- Status Selector -->
          <div class="space-y-1.5">
            <div class="text-sm text-ink-gray-5">{{ __("Status") }}</div>
            <div class="relative flex items-center">
              <TaskStatusIcon
                :status="form.status || 'Todo'"
                class="absolute left-3 z-10 h-4 w-4 pointer-events-none"
              />
              <FormControl
                type="select"
                variant="subtle"
                class="w-full !pl-9"
                :options="statusOptions"
                v-model="form.status"
              />
            </div>
          </div>
        </div>
      </div>
    </template>

    <template #actions>
      <div class="flex justify-end pt-2">
        <Button
          :label="isEditing ? __('Update') : __('Create')"
          variant="solid"
          :loading="loading"
          :disabled="loading"
          @click="handleSubmit"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";
import {
  Autocomplete,
  Avatar,
  Button,
  DateTimePicker,
  Dialog,
  FormControl,
  FeatherIcon,
  TextInput,
  call,
  toast,
} from "frappe-ui";
import { __ } from "@/translation";
import { isContentEmpty } from "@/utils";
import { useUserStore } from "@/stores/user";
import CompactEditor from "@/components/CompactEditor.vue";
import TaskStatusIcon from "@/components/icons/TaskStatusIcon.vue";
import TaskPriorityIcon from "@/components/icons/TaskPriorityIcon.vue";

// --- Props & Emits ---
const props = defineProps({
  modelValue: { type: Boolean, default: false },
  task: { type: Object, default: null },
  ticketId: { type: [String, Number], default: "" },
});

const emit = defineEmits(["update:modelValue", "submit"]);

// --- Store ---
const { getUser, agentOptions } = useUserStore();

// --- State Layout ---
const show = computed({
  get: () => props.modelValue,
  set: (value) => emit("update:modelValue", value),
});

const loading = ref(false);
const titleRef = ref(null);
const activeTask = ref<any>(null);

const isEditing = computed(
  () => !!(props.task?.name || activeTask.value?.name)
);

const defaultForm = () => ({
  title: "",
  description: "",
  due_date: "",
  status: "Backlog",
  priority: "Low",
  assigned: "",
});

const form = ref(defaultForm());

const errors = ref({
  title: false,
  titleLength: false,
  description: false,
  descriptionLength: false,
});

const getDescriptionLength = computed(() => {
  if (!form.value.description) return 0;
  return form.value.description.length;
});

watch(
  () => form.value.title,
  (val) => {
    if (val?.trim()) errors.value.title = false;
    if (val?.length <= 140) errors.value.titleLength = false;
  }
);

watch(
  () => form.value.description,
  (val) => {
    if (!isContentEmpty(val)) errors.value.description = false;
    if (!val || val.length <= 4000) errors.value.descriptionLength = false;
  }
);

const assigneeLabel = computed(() => {
  if (!form.value.assigned) return "";
  const fromList = agentOptions.find((o) => o.value === form.value.assigned);
  if (fromList?.label) return fromList.label;
  const storeUser = getUser(form.value.assigned);
  if (storeUser?.full_name) return storeUser.full_name;
  return form.value.assigned;
});

function getAssigneeImage(assigned: string): string {
  const fromList = agentOptions.find((o) => o.value === assigned);
  if (fromList?.image) return fromList.image;
  return getUser(assigned)?.user_image || "";
}

function handleAssigneeChange(option: any) {
  if (!option) form.value.assigned = "";
  else if (typeof option === "object") form.value.assigned = option.value || "";
  else form.value.assigned = option;
}

function resolveAssigned(): string {
  if (form.value.assigned?.trim()) return form.value.assigned;
  const sessionUser = window.session_user;
  return sessionUser && sessionUser !== "Guest" ? sessionUser : "";
}

watch(
  () => props.task,
  (task) => {
    errors.value.title = false;
    errors.value.titleLength = false;
    errors.value.description = false;
    errors.value.descriptionLength = false;

    form.value = task
      ? {
          title: task.title || "",
          description: task.description || "",
          due_date: task.due_date || "",
          status: task.status || "Backlog",
          priority: task.priority || "Low",
          assigned: task.assigned || "",
        }
      : defaultForm();
  },
  { immediate: true, deep: true }
);

watch(show, async (val) => {
  if (!val) {
    activeTask.value = null;
    return;
  }

  errors.value.title = false;
  errors.value.titleLength = false;
  errors.value.description = false;
  errors.value.descriptionLength = false;

  if (!props.task && !activeTask.value) {
    form.value = defaultForm();
    form.value.assigned = resolveAssigned();
  }

  nextTick(() => setTimeout(() => (titleRef.value as any)?.el?.focus?.(), 100));
});

const statusOptions = [
  { label: __("Backlog"), value: "Backlog" },
  { label: __("Todo"), value: "Todo" },
  { label: __("In Progress"), value: "In Progress" },
  { label: __("Done"), value: "Done" },
  { label: __("Canceled"), value: "Canceled" },
];

const priorityOptions = [
  { label: __("Low"), value: "Low" },
  { label: __("Medium"), value: "Medium" },
  { label: __("High"), value: "High" },
];

function showTask(task: any) {
  errors.value.title = false;
  errors.value.titleLength = false;
  errors.value.description = false;
  errors.value.descriptionLength = false;

  form.value = {
    title: task.title || "",
    description: task.description || "",
    due_date: task.due_date || "",
    status: task.status || "Backlog",
    priority: task.priority || "Low",
    assigned: task.assigned || "",
  };
  activeTask.value = task;
  show.value = true;
}

async function updateTaskStatus(task: any, newStatus: string) {
  if (!task?.name) {
    toast.error(__("Task not found"));
    return;
  }
  try {
    await call("helpdesk.helpdesk.doctype.hd_task.hd_task.update_task", {
      task: task.name,
      status: newStatus,
    });
    toast.success(__("Status updated"));
    emit("submit", { ...task, status: newStatus });
  } catch (e: any) {
    const msg =
      e?.message ||
      e?.exc?.split("\n").filter(Boolean).pop() ||
      __("Something went wrong");
    toast.error(msg);
  }
}

defineExpose({ showTask, updateTaskStatus });

async function handleSubmit() {
  errors.value.title = false;
  errors.value.titleLength = false;
  errors.value.description = false;
  errors.value.descriptionLength = false;

  let formsAreInvalid = false;

  if (!form.value.title?.trim()) {
    errors.value.title = true;
    formsAreInvalid = true;
  } else if (form.value.title.length > 140) {
    errors.value.titleLength = true;
    formsAreInvalid = true;
  }

  if (isContentEmpty(form.value.description)) {
    errors.value.description = true;
    formsAreInvalid = true;
  } else if (form.value.description.length > 4000) {
    errors.value.descriptionLength = true;
    formsAreInvalid = true;
  }

  if (formsAreInvalid) {
    toast.error(__("Please fix validation issues before updating."));
    return;
  }

  if (loading.value) return;
  loading.value = true;
  const targetAssignee = resolveAssigned() || null;

  try {
    let result: any;

    if (isEditing.value) {
      const taskName = props.task?.name || activeTask.value?.name;
      result = await call(
        "helpdesk.helpdesk.doctype.hd_task.hd_task.update_task",
        {
          task: taskName,
          title: form.value.title,
          description: isContentEmpty(form.value.description)
            ? null
            : form.value.description,
          due_date: form.value.due_date || null,
          status: form.value.status,
          priority: form.value.priority,
          assigned: targetAssignee, // FIX 2: Replaced broken undefined variable layout reference
        }
      );

      if (!result || typeof result !== "object" || !result.name) {
        result = {
          name: taskName,
          title: form.value.title,
          description: form.value.description,
          due_date: form.value.due_date,
          status: form.value.status,
          priority: form.value.priority,
          assigned: targetAssignee,
        };
      }
      toast.success(__("Task updated"));
    } else {
      const ticketId = String(props.ticketId || "").trim();
      if (!ticketId) {
        toast.error(__("Ticket ID is missing"));
        loading.value = false;
        return;
      }
      result = await call(
        "helpdesk.helpdesk.doctype.hd_task.hd_task.create_task",
        {
          ticket: ticketId,
          title: form.value.title,
          description: isContentEmpty(form.value.description)
            ? null
            : form.value.description,
          due_date: form.value.due_date || null,
          status: form.value.status,
          priority: form.value.priority,
          assigned: targetAssignee,
        }
      );
      toast.success(__("Task created"));
    }

    emit("submit", result);
    show.value = false;
    activeTask.value = null;
  } catch (e: any) {
    const msg =
      e?.message ||
      e?.exc?.split("\n").filter(Boolean).pop() ||
      __("Something went wrong");
    toast.error(msg);
  } finally {
    loading.value = false;
  }
}
</script>
