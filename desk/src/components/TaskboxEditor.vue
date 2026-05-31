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

        <div class="space-y-1.5">
          <div class="flex items-center justify-between">
            <div class="text-sm text-ink-gray-5 flex items-center gap-1">
              {{ __('Title') }} <span class="text-red-500">*</span>
            </div>
            <span 
              class="text-xs transition-colors"
              :class="form.title.length > 140 ? 'text-red-500 font-semibold' : 'text-ink-gray-4'"
            >
              {{ form.title.length }}/140
            </span>
          </div>
          <TextInput
            ref="titleRef"
            v-model="form.title"
            variant="subtle"
            class="w-full rounded-md transition-all border"
            :class="{ 'border-red-500 ring-1 ring-red-500 focus:border-red-500 focus:ring-red-500': errors.title || errors.titleLength }"
            :placeholder="__('Enter task title')"
          />
          <p v-if="errors.title" class="text-xs text-red-500 font-medium">
            {{ __('Title is required') }}
          </p>
          <p v-if="errors.titleLength" class="text-xs text-red-500 font-medium">
            {{ __('Title cannot exceed 140 characters') }}
          </p>
        </div>

        <div class="space-y-1.5">
          <div class="flex items-center justify-between">
            <div class="text-sm text-ink-gray-5 flex items-center gap-1">
              {{ __("Description") }} <span class="text-red-500">*</span>
            </div>
            <span 
              class="text-xs transition-colors"
              :class="getDescriptionLength > 4000 ? 'text-red-500 font-semibold' : 'text-ink-gray-4'"
            >
              {{ getDescriptionLength }}/4000
            </span>
          </div>
          <TextEditor
            :editor-class="`!prose-sm max-w-full overflow-auto min-h-[180px] max-h-80 py-1.5 px-2 rounded-b border bg-surface-gray-2 placeholder-ink-gray-4 hover:shadow-sm focus:bg-surface-white focus:shadow-sm focus:ring-0 focus-visible:ring-2 text-ink-gray-8 transition-colors -mt-0.5 ${
              (errors.description || errors.descriptionLength)
                ? 'border-red-500 focus-visible:ring-red-500' 
                : 'border-[--surface-gray-2] hover:border-outline-gray-modals focus:border-outline-gray-4 focus-visible:ring-outline-gray-3'
            }`"
            :bubble-menu="false"
            :fixed-menu="true"
            :content="form.description"
            :placeholder="__('Enter task description...')"
            @change="(val) => (form.description = val)"
          />
          <p v-if="errors.description" class="text-xs text-red-500 font-medium">
            {{ __('Description is required') }}
          </p>
          <p v-if="errors.descriptionLength" class="text-xs text-red-500 font-medium">
            {{ __('Description exceeds character limit (Max 4,000)') }}
          </p>
        </div>

        <div class="grid grid-cols-2 gap-4">

          <div class="space-y-1.5">
            <div class="text-sm text-ink-gray-5">{{ __('Priority') }}</div>
            <FormControl
              type="select"
              variant="subtle"
              :options="priorityOptions"
              v-model="form.priority"
            />
          </div>

          <div class="space-y-1.5">
            <div class="text-sm text-ink-gray-5">{{ __('Assigned To') }}</div>
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
                    <span class="truncate">{{ assigneeLabel || __('Assigned To') }}</span>
                  </div>
                  <template #suffix>
                    <FeatherIcon name="chevron-down" class="h-4 w-4 text-ink-gray-5" />
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

          <div class="space-y-1.5">
            <div class="text-sm text-ink-gray-5">{{ __('Due Date') }}</div>
            <div class="w-full date-picker-wrapper">
              <DateTimePicker
                v-model="form.due_date"
                :placeholder="__('Due Date')"
                format="DD-MM-YYYY HH:mm"
              />
            </div>
          </div>

          <div class="space-y-1.5">
            <div class="text-sm text-ink-gray-5">{{ __('Status') }}</div>
            <FormControl
              type="select"
              variant="subtle"
              :options="statusOptions"
              v-model="form.status"
            />
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
  TextEditor,
  TextInput,
  call,
  createResource,
  toast,
} from "frappe-ui";
import { __ } from "@/translation";
import { isContentEmpty } from "@/utils";
import { useUserStore } from "@/stores/user";

// --- Props & Emits ---
const props = defineProps({
  modelValue: { type: Boolean, default: false },
  task:       { type: Object, default: null },
  ticketId:   { type: [String, Number], default: "" },
});

const emit = defineEmits(["update:modelValue", "submit"]);

// --- Store ---
const { getUser } = useUserStore();

// --- State ---
const show = computed({
  get: () => props.modelValue,
  set: (value) => emit("update:modelValue", value),
});

const loading    = ref(false);
const titleRef   = ref(null);
const activeTask = ref<any>(null);

const isEditing = computed(() => !!(props.task?.name || activeTask.value?.name));

const defaultForm = () => ({
  title:       "",
  description: "",
  due_date:    "",
  status:      "Backlog",
  priority:    "Low",
  assigned:    "",
});

const form = ref(defaultForm());

// --- Validation States ---
const errors = ref({
  title: false,
  titleLength: false,
  description: false,
  descriptionLength: false,
});

// Safe counter fallback helper for Description string length evaluation
const getDescriptionLength = computed(() => {
  if (!form.value.description) return 0;
  // If HTML elements are involved, you can map out raw length safely
  return form.value.description.length;
});

// Instantly scrub warning nodes when criteria are successfully met while editing
watch(() => form.value.title, (val) => {
  if (val?.trim()) errors.value.title = false;
  if (val?.length <= 140) errors.value.titleLength = false;
});

watch(() => form.value.description, (val) => {
  if (!isContentEmpty(val)) errors.value.description = false;
  if (!val || val.length <= 4000) errors.value.descriptionLength = false;
});

// --- Users/Agents Logic ---
const agentsList = createResource({
  url: "frappe.client.get_list",
  params: {
    doctype:     "User",
    fields:      ["name", "full_name", "user_image"],
    filters:     { enabled: 1, user_type: "System User" },
    page_length: 200,
  },
  auto: true,
});

const agentOptions = computed(() => {
  if (!agentsList.data) return [];
  return (agentsList.data as any[]).map((u: any) => ({
    label: u.full_name || u.name,
    value: u.name,
    image: u.user_image || "",
  }));
});

const assigneeLabel = computed(() => {
  if (!form.value.assigned) return "";

  const fromList = agentOptions.value.find((o) => o.value === form.value.assigned);
  if (fromList?.label) return fromList.label;

  const storeUser = getUser(form.value.assigned);
  if (storeUser?.full_name) return storeUser.full_name;

  return form.value.assigned
    .split("@")[0]
    .split(/[._-]/)
    .map((w: string) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
});

function getAssigneeImage(assigned: string): string {
  const fromList = agentOptions.value.find((o) => o.value === assigned);
  if (fromList?.image) return fromList.image;
  return getUser(assigned)?.user_image || "";
}

function handleAssigneeChange(option: any) {
  if (!option)                         form.value.assigned = "";
  else if (typeof option === "object") form.value.assigned = option.value || "";
  else                                 form.value.assigned = option;
}

function resolveAssigned(): string {
  if (form.value.assigned?.trim()) return form.value.assigned;
  const sessionUser = window.session_user;
  return sessionUser && sessionUser !== "Guest" ? sessionUser : "";
}

// --- Watchers ---
watch(
  () => props.task,
  (task) => {
    errors.value.title = false;
    errors.value.titleLength = false;
    errors.value.description = false;
    errors.value.descriptionLength = false;

    if (task) {
      form.value = {
        title:       task.title       || "",
        description: task.description || "",
        due_date:    task.due_date    || "",
        status:      task.status      || "Backlog",
        priority:    task.priority    || "Low",
        assigned:    task.assigned    || "",
      };
    } else {
      form.value = defaultForm();
    }
  },
  { immediate: true, deep: true },
);

watch(show, async (val) => {
  if (!val) return;

  errors.value.title = false;
  errors.value.titleLength = false;
  errors.value.description = false;
  errors.value.descriptionLength = false;
  
  await agentsList.fetch();

  if (!props.task && !activeTask.value) {
    form.value = defaultForm();
    form.value.assigned = resolveAssigned();
  }

  nextTick(() => setTimeout(() => (titleRef.value as any)?.el?.focus?.(), 100));
});

// --- Options ---
const statusOptions = [
  { label: __("Backlog"),     value: "Backlog"      },
  { label: __("Todo"),        value: "Todo"         },
  { label: __("In Progress"), value: "In Progress"  },
  { label: __("Done"),        value: "Done"         },
  { label: __("Canceled"),    value: "Canceled"     },
];

const priorityOptions = [
  { label: __("Low"),    value: "Low"    },
  { label: __("Medium"), value: "Medium" },
  { label: __("High"),   value: "High"   },
];

// --- Exposed methods ---
function showTask(task: any) {
  errors.value.title = false;
  errors.value.titleLength = false;
  errors.value.description = false;
  errors.value.descriptionLength = false;

  form.value = {
    title:       task.title       || "",
    description: task.description || "",
    due_date:    task.due_date    || "",
    status:      task.status      || "Backlog",
    priority:    task.priority    || "Low",
    assigned:    task.assigned    || "",
  };
  activeTask.value = task;
  show.value = true;
}

async function updateTaskStatus(task: any, newStatus: string) {
  if (!task?.name) { toast.error(__("Task not found")); return; }
  try {
    await call("helpdesk.helpdesk.doctype.hd_task.hd_task.update_task", {
      task:   task.name,
      status: newStatus,
    });
    toast.success(__("Status updated"));
    emit("submit", { ...task, status: newStatus });
  } catch (e: any) {
    const msg = e?.message || e?.exc?.split("\n").filter(Boolean).pop() || __("Something went wrong");
    toast.error(msg);
  }
}

async function deleteTask(taskName: string) {
  if (!taskName || typeof taskName !== "string" || !taskName.trim()) {
    toast.error(__("Task not found"));
    return;
  }
  try {
    await call("helpdesk.helpdesk.doctype.hd_task.hd_task.delete_task", {
      task: taskName,
    });
    toast.success(__("Task deleted"));
    emit("submit", null);
  } catch (e: any) {
    const msg = e?.message || e?.exc?.split("\n").filter(Boolean).pop() || __("Something went wrong");
    toast.error(msg);
  }
}

defineExpose({ showTask, updateTaskStatus, deleteTask });

// --- Actions ---
async function handleSubmit() {
  errors.value.title = false;
  errors.value.titleLength = false;
  errors.value.description = false;
  errors.value.descriptionLength = false;

  let formsAreInvalid = false;

  // 1. Check Title Empty & Length States
  if (!form.value.title?.trim()) {
    errors.value.title = true;
    formsAreInvalid = true;
  } else if (form.value.title.length > 140) {
    errors.value.titleLength = true;
    formsAreInvalid = true;
  }
  
  // 2. Check Description Empty & Length States
  if (isContentEmpty(form.value.description)) {
    errors.value.description = true;
    formsAreInvalid = true;
  } else if (form.value.description.length > 4000) {
    errors.value.descriptionLength = true;
    formsAreInvalid = true;
  }

  // 3. Stop submission execution instantly on validation faults
  if (formsAreInvalid) {
    toast.error(__("Please fix validation issues before updating."));
    return;
  }

  if (loading.value) return;
  loading.value = true;

  try {
    let result: any;
    const dbDate    = form.value.due_date || null;
    const assignedTo = resolveAssigned();

    if (isEditing.value) {
      const taskName = props.task?.name || activeTask.value?.name;
      result = await call("helpdesk.helpdesk.doctype.hd_task.hd_task.update_task", {
        task:        taskName,
        title:       form.value.title,
        description: isContentEmpty(form.value.description) ? null : form.value.description,
        due_date:    dbDate,
        status:      form.value.status,
        priority:    form.value.priority,
        assigned:    assignedTo,
      });
      toast.success(__("Task updated"));
    } else {
      const ticketId = String(props.ticketId || "").trim();
      if (!ticketId) { toast.error(__("Ticket ID is missing")); loading.value = false; return; }
      result = await call("helpdesk.helpdesk.doctype.hd_task.hd_task.create_task", {
        ticket:      ticketId,
        title:       form.value.title,
        description: isContentEmpty(form.value.description) ? null : form.value.description,
        due_date:    dbDate,
        status:      form.value.status,
        priority:    form.value.priority,
        assigned:    assignedTo,
      });
      toast.success(__("Task created"));
    }

    emit("submit", result);
    show.value   = false;
    activeTask.value = null;
  } catch (e: any) {
    const msg = e?.message || e?.exc?.split("\n").filter(Boolean).pop() || __("Something went wrong");
    toast.error(msg);
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.date-picker-wrapper :deep(input) {
  width: 100%;
  background-color: var(--surface-gray-2, #f3f4f6);
  border: none;
  box-shadow: none;
}
.date-picker-wrapper :deep(input:focus) {
  background-color: white;
  border-color: #d1d5db;
  box-shadow: 0 0 0 1px #d1d5db;
}
</style>