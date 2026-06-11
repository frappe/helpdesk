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
        <!-- Title -->
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
              'border-red-500 ring-1 ring-red-500':
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

        <!-- Description -->
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
          <TextEditor
            :editor-class="`!prose-sm max-w-full overflow-auto min-h-[180px] max-h-80 py-1.5 px-2 rounded-b border bg-surface-gray-2 placeholder-ink-gray-4 hover:shadow-sm focus:bg-surface-white focus:shadow-sm focus:ring-0 focus-visible:ring-2 text-ink-gray-8 transition-colors -mt-0.5 ${
              errors.description || errors.descriptionLength
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
            {{ __("Description is required") }}
          </p>
          <p
            v-if="errors.descriptionLength"
            class="text-xs text-red-500 font-medium"
          >
            {{ __("Description exceeds character limit (Max 4,000)") }}
          </p>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <!-- Priority -->
          <div class="space-y-1.5">
            <div class="text-sm text-ink-gray-5">{{ __("Priority") }}</div>
            <FormControl
              type="select"
              variant="subtle"
              :options="priorityOptions"
              v-model="form.priority"
            />
          </div>

          <!-- Assigned To -->
          <div class="space-y-1.5">
            <div class="text-sm text-ink-gray-5">{{ __("Assigned To") }}</div>
            <Autocomplete
              :options="filteredAgentOptions"
              :value="form.assigned"
              @change="handleAssigneeChange"
              @input-change="searchAgents"
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

          <!-- Due Date -->
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

          <!-- Status -->
          <div class="space-y-1.5">
            <div class="text-sm text-ink-gray-5">{{ __("Status") }}</div>
            <FormControl
              type="select"
              variant="subtle"
              :options="statusOptions"
              v-model="form.status"
            />
          </div>

          <!-- Ticket ID -->
          <div v-if="!props.ticketId" class="space-y-1.5 col-span-2">
            <div class="text-sm text-ink-gray-5">
              {{ __("Ticket") }} <span class="text-red-500">*</span>
            </div>
            <Autocomplete
              :options="ticketOptions"
              :value="form.ticket"
              @change="handleTicketChange"
              @input-change="searchTickets"
              :placeholder="__('Search ticket by ID or subject...')"
              class="w-full"
            >
              <template #target="{ togglePopover }">
                <Button
                  variant="subtle"
                  class="w-full flex items-center justify-between font-normal text-ink-gray-8"
                  @click="togglePopover"
                >
                  <span class="truncate">
                    {{ ticketLabel || __("Search ticket by ID or subject...") }}
                  </span>
                  <template #suffix>
                    <FeatherIcon
                      name="chevron-down"
                      class="h-4 w-4 text-ink-gray-5"
                    />
                  </template>
                </Button>
              </template>
            </Autocomplete>
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
import { storeToRefs } from "pinia";
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
  toast,
} from "frappe-ui";
import { __ } from "@/translation";
import { isContentEmpty } from "@/utils";
import { useUserStore } from "@/stores/user";

// ─── Props & Emits
const props = defineProps({
  modelValue: { type: Boolean, default: false },
  task: { type: Object, default: null },
  ticketId: { type: [String, Number], default: "" },
});

const emit = defineEmits(["update:modelValue", "submit", "task-created"]);

// ─── Store
const userStore = useUserStore();
const { getUser } = userStore;
const { agentOptions } = storeToRefs(userStore);

// ─── Dialog visibility
const show = computed({
  get: () => props.modelValue,
  set: (value) => emit("update:modelValue", value),
});

// ─── Local state
const loading = ref(false);
const titleRef = ref(null);
const activeTask = ref<any>(null);
const agentQuery = ref("");

const isEditing = computed(
  () => !!(props.task?.name || activeTask.value?.name)
);

// ─── Form
const defaultForm = () => ({
  title: "",
  description: "",
  due_date: "",
  status: "Backlog",
  priority: "Low",
  assigned: "",
  ticket: "",
});

const form = ref(defaultForm());

// ─── Validation
const errors = ref({
  title: false,
  titleLength: false,
  description: false,
  descriptionLength: false,
});

const getDescriptionLength = computed(() =>
  form.value.description ? form.value.description.length : 0
);

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

// ─── Assignee
const normalizedAgentOptions = computed(() =>
  (agentOptions.value || []).map((agent) => ({
    // Fixed: Added .value to match the ref mapping
    label: agent.label || agent.title || agent.value || "",
    value: agent.value,
    image: agent.image,
  }))
);

const filteredAgentOptions = computed(() => {
  const query = agentQuery.value.toLowerCase().trim();
  if (!query) return normalizedAgentOptions.value;
  return normalizedAgentOptions.value.filter(
    (o) =>
      o.label.toLowerCase().includes(query) ||
      o.value.toLowerCase().includes(query)
  );
});

function searchAgents(query: string) {
  agentQuery.value = query;
}

const assigneeLabel = computed(() => {
  if (!form.value.assigned) return "";
  const fromList = normalizedAgentOptions.value.find(
    (o) => o.value === form.value.assigned
  );
  if (fromList?.label) return fromList.label;
  return getUser(form.value.assigned)?.full_name || form.value.assigned;
});

function getAssigneeImage(assigned: string): string {
  const fromList = normalizedAgentOptions.value.find(
    (o) => o.value === assigned
  );
  if (fromList?.image) return fromList.image;
  return getUser(assigned)?.user_image || "";
}

function handleAssigneeChange(option: any) {
  if (!option) form.value.assigned = "";
  else if (typeof option === "object") form.value.assigned = option.value || "";
  else form.value.assigned = option;
  agentQuery.value = "";
}

// ─── Ticket search
const ticketOptions = ref<{ label: string; value: string }[]>([]);
const ticketSearching = ref(false);

const ticketLabel = computed(() => {
  if (!form.value.ticket) return "";
  return (
    ticketOptions.value.find((o) => o.value === form.value.ticket)?.label ||
    form.value.ticket
  );
});

async function searchTickets(query: string) {
  if (ticketSearching.value) return;
  ticketSearching.value = true;
  try {
    const results = await call("frappe.client.get_list", {
      doctype: "HD Ticket",
      fields: ["name", "subject"],
      filters: query ? [["HD Ticket", "subject", "like", `%${query}%`]] : [],
      limit: 20,
      order_by: "modified desc",
    });
    ticketOptions.value = (results || []).map((t: any) => ({
      label: `#${t.name} — ${t.subject || "No subject"}`,
      value: String(t.name),
    }));
  } catch {
    ticketOptions.value = [];
  } finally {
    ticketSearching.value = false;
  }
}

function handleTicketChange(option: any) {
  if (!option) form.value.ticket = "";
  else if (typeof option === "object") form.value.ticket = option.value || "";
  else form.value.ticket = option;
}

// ─── Helpers
function clearErrors() {
  errors.value = {
    title: false,
    titleLength: false,
    description: false,
    descriptionLength: false,
  };
}

function formFromTask(task: any) {
  return {
    title: task.title || "",
    description: task.description || "",
    due_date: task.due_date || "",
    status: task.status || "Backlog",
    priority: task.priority || "Low",
    assigned: task.assigned || "",
    ticket: task.reference_docname || String(props.ticketId || ""),
  };
}

// ─── Watchers
watch(
  () => props.task,
  (task) => {
    clearErrors();
    form.value = task
      ? formFromTask(task)
      : { ...defaultForm(), ticket: String(props.ticketId || "") };
  },
  { immediate: true, deep: true }
);

watch(show, async (val) => {
  clearErrors();
  agentQuery.value = "";

  if (!val) {
    activeTask.value = null;
    form.value = defaultForm();
    return;
  }

  if (!props.ticketId) searchTickets("");

  if (!props.task && !activeTask.value) {
    form.value = { ...defaultForm(), ticket: String(props.ticketId || "") };
  }

  nextTick(() => setTimeout(() => (titleRef.value as any)?.el?.focus?.(), 100));
});

// ─── Options
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
  clearErrors();
  activeTask.value = task;
  form.value = formFromTask(task);
  show.value = true;
}

async function updateTaskStatus(task: any, newStatus: string) {
  if (!task?.name) {
    toast.error(__("Task not found"));
    return;
  }
  try {
    const result = await call(
      "helpdesk.helpdesk.doctype.hd_task.hd_task.update_task",
      {
        task: task.name,
        status: newStatus,
      }
    );
    toast.success(__("Status updated"));
    const saved = result?.message ?? result;
    emit(
      "submit",
      saved && typeof saved === "object"
        ? saved
        : { ...task, status: newStatus }
    );
    emit("task-created");
  } catch (e: any) {
    const msg =
      e?.message ||
      e?.exc?.split("\n").filter(Boolean).pop() ||
      __("Something went wrong");
    toast.error(msg);
    throw e;
  }
}

defineExpose({ showTask, updateTaskStatus });

async function handleSubmit() {
  clearErrors();

  let invalid = false;

  if (!form.value.title?.trim()) {
    errors.value.title = true;
    invalid = true;
  } else if (form.value.title.length > 140) {
    errors.value.titleLength = true;
    invalid = true;
  }

  if (isContentEmpty(form.value.description)) {
    errors.value.description = true;
    invalid = true;
  } else if (form.value.description.length > 4000) {
    errors.value.descriptionLength = true;
    invalid = true;
  }

  if (invalid) {
    toast.error(__("Please fix validation issues before submitting."));
    return;
  }

  if (loading.value) return;
  loading.value = true;

  try {
    let result: any;
    const dbDate = form.value.due_date || null;
    const assignedTo = form.value.assigned?.trim() || "";

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
          due_date: dbDate,
          status: form.value.status,
          priority: form.value.priority,
          assigned: assignedTo,
        }
      );
      toast.success(__("Task updated"));
    } else {
      const ticketId = String(form.value.ticket || props.ticketId || "").trim();
      if (!ticketId) {
        toast.error(__("Ticket ID is required to create a task"));
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
          due_date: dbDate,
          status: form.value.status,
          priority: form.value.priority,
          assigned: assignedTo,
        }
      );
      toast.success(__("Task created"));
    }

    emit("submit", result);
    emit("task-created");
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
