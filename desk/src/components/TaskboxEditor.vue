<template>
  <Dialog v-model="show" :options="{ size: 'xl' }">
    <template #body-title>
      <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
        {{ isEditing ? __("Edit Task") : __("Create Task") }}
      </h3>
    </template>

    <template #body-content>
      <div class="flex flex-col gap-4">

        <!-- TITLE -->
        <div class="space-y-1.5">
          <FormLabel :label="__('Title')" required />
          <TextInput
            ref="titleRef"
            v-model="form.title"
            :placeholder="__('Enter task title')"
          />
        </div>

        <!-- DESCRIPTION -->
        <div>
          <div class="mb-1.5 text-xs text-ink-gray-5">{{ __("Description") }}</div>
          <TextEditor
            variant="outline"
            editor-class="!prose-sm overflow-auto min-h-[180px] max-h-80 py-1.5 px-2 rounded border border-[--surface-gray-2]"
            :bubbleMenu="true"
            :content="form.description"
            :placeholder="__('Task description')"
            @change="(val) => (form.description = val)"
          />
        </div>

        <!--
          CONTROLS ROW — Image 2 style:
          • borderless pill buttons
          • Status: icon + text, no chevron
          • Assignee: avatar + name + chevron (dropdown)
          • Date: input + chevron (dropdown)
          • Priority: plain text, no chevron, no border
          All sit flush left in a single flex row.
        -->
        <div class="flex flex-row flex-nowrap items-center gap-2">

          <!-- STATUS — no chevron, borderless -->
          <Dropdown :options="statusDropdownOptions">
            <button class="pill pill-ghost">
              <TaskStatusIcon :status="form.status" class="pill-icon" />
              <span>{{ form.status }}</span>
            </button>
          </Dropdown>

          <!-- ASSIGNEE — avatar + name + chevron -->
          <Autocomplete
            :options="agentOptions"
            :value="form.assigned"
            @change="handleAssigneeChange"
            :placeholder="__('Assign To')"
          >
            <template #target="{ togglePopover }">
              <button class="pill pill-ghost" @click="togglePopover">
                <Avatar
                  v-if="form.assigned"
                  class="!h-4 !w-4 flex-shrink-0"
                  shape="circle"
                  :label="assigneeLabel"
                  :image="getAssigneeImage(form.assigned)"
                />
                <FeatherIcon v-else name="user" class="pill-icon text-ink-gray-4" />
                <span>{{ assigneeLabel || __("Assign To") }}</span>
                <FeatherIcon name="chevron-down" class="pill-chevron" />
              </button>
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

          <!-- DUE DATE + TIME — DateTimePicker so full datetime is saved -->
          <div class="pill-datepicker">
            <DateTimePicker
              v-model="form.due_date"
              :placeholder="__('Due date')"
              :formatter="formatPickerDate"
            />
          </div>

          <!-- PRIORITY — plain text, no border -->
          <Dropdown :options="priorityDropdownOptions">
            <button class="pill pill-ghost">
              <span>{{ form.priority }}</span>
              <FeatherIcon name="chevron-down" class="pill-chevron" />
            </button>
          </Dropdown>

        </div>
      </div>
    </template>

    <template #actions>
      <div class="flex justify-end">
        <Button
          :label="isEditing ? __('Update') : __('Create')"
          variant="solid"
          :loading="loading"
          :disabled="!form.title?.trim() || loading"
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
  Dropdown,
  FeatherIcon,
  FormLabel,
  TextEditor,
  TextInput,
  call,
  createResource,
  toast,
} from "frappe-ui";
import { __ } from "@/translation";
import { isContentEmpty } from "@/utils";
import TaskStatusIcon from "@/components/icons/TaskStatusIcon.vue";

const props = defineProps({
  task:     { type: Object, default: null },
  ticketId: { type: [String, Number], default: "" },
});

const show     = defineModel({ type: Boolean });
const emit     = defineEmits(["submit"]);
const loading  = ref(false);
const titleRef = ref(null);

const isEditing = computed(() => !!props.task?.name);



const defaultForm = () => ({
  title: "", description: "", due_date: "",
  status: "Backlog", priority: "Low", assigned: "",
});

const form = ref(defaultForm());



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
  const match = agentOptions.value.find((o) => o.value === form.value.assigned);
  if (match) return match.label;
  return form.value.assigned.split("@")[0]
    .split(/[._-]/)
    .map((w: string) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
});

function getAssigneeImage(assigned: string): string {
  return agentOptions.value.find((o) => o.value === assigned)?.image || "";
}

function formatPickerDate(date: Date | string | null): string {
  if (!date) return "";
  const d = typeof date === "string" ? new Date(date) : date;
  if (isNaN(d.getTime())) return "";
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function handleAssigneeChange(option: any) {
  if (!option)                         form.value.assigned = "";
  else if (typeof option === "object") form.value.assigned = option.value || "";
  else                                 form.value.assigned = option;
}


watch(
  () => props.task,
  (task) => {
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

watch(show, (val) => {
  if (val) {
    if (!props.task) form.value = defaultForm();
    agentsList.fetch();
    nextTick(() => setTimeout(() => (titleRef.value as any)?.el?.focus?.(), 100));
  }
});


const statusDropdownOptions = computed(() => [
  { label: __("Backlog"),     onClick: () => (form.value.status = "Backlog") },
  { label: __("Todo"),        onClick: () => (form.value.status = "Todo") },
  { label: __("In Progress"), onClick: () => (form.value.status = "In Progress") },
  { label: __("Done"),        onClick: () => (form.value.status = "Done") },
  { label: __("Canceled"),    onClick: () => (form.value.status = "Canceled") },
]);

const priorityDropdownOptions = computed(() => [
  { label: __("Low"),    onClick: () => (form.value.priority = "Low") },
  { label: __("Medium"), onClick: () => (form.value.priority = "Medium") },
  { label: __("High"),   onClick: () => (form.value.priority = "High") },
]);



async function handleSubmit() {
  if (!form.value.title?.trim()) { toast.error(__("Title is required")); return; }
  if (loading.value) return;
  loading.value = true;

  try {
    let result: any;
    const dbDate = form.value.due_date || null;

    if (isEditing.value) {
      result = await call("helpdesk.helpdesk.doctype.hd_task.hd_task.update_task", {
        task:        props.task.name,
        title:       form.value.title,
        description: isContentEmpty(form.value.description) ? null : form.value.description,
        due_date:    dbDate,
        status:      form.value.status,
        priority:    form.value.priority,
        assigned:    form.value.assigned || null,
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
        assigned:    form.value.assigned || null,
      });
      toast.success(__("Task created"));
    }

    emit("submit", result);
    show.value = false;
  } catch (e: any) {
    const msg = e?.message || e?.exc?.split("\n").filter(Boolean).pop() || __("Something went wrong");
    toast.error(msg);
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.pill {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  height: 2rem;
  padding: 0 0.625rem;
  font-size: 0.875rem;
  font-weight: 500;
  white-space: nowrap;
  border-radius: 0.5rem;
  cursor: pointer;
  border: none;
  transition: background 0.12s;
}


.pill-ghost {
  background: var(--surface-gray-2, #f3f4f6);
  color: var(--ink-gray-8, #1f2937);
}
.pill-ghost:hover {
  background: var(--surface-gray-3, #e5e7eb);
}

.pill-icon    { width: 1rem; height: 1rem; flex-shrink: 0; }
.pill-chevron { width: 0.75rem; height: 0.75rem; flex-shrink: 0; color: var(--ink-gray-4, #9ca3af); margin-left: 0.125rem; }


.pill-datepicker {
  flex-shrink: 0;
  max-width: 8.5rem;  
}

/* Force the wrapper and any inner container to respect max-width */
.pill-datepicker :deep(*) {
  max-width: 100% !important;
}

.pill-datepicker :deep(input) {
  height: 2rem !important;
  width: 8.5rem !important;
  max-width: 8.5rem !important;
  padding: 0 0.625rem !important;
  font-size: 0.875rem !important;
  font-weight: 500 !important;
  border-radius: 0.5rem !important;
  border: none !important;
  background: var(--surface-gray-2, #f3f4f6) !important;
  color: var(--ink-gray-8, #1f2937) !important;
  cursor: pointer !important;
  outline: none !important;
  transition: background 0.12s;
}

.pill-datepicker :deep(input):hover {
  background: var(--surface-gray-3, #e5e7eb) !important;
}

.pill-datepicker :deep(.datepicker),
.pill-datepicker :deep(.datepicker-container) {
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
  width: auto !important;
}


.pill-datepicker :deep(svg),
.pill-datepicker :deep(.datepicker-toggle) {
  display: none !important;
}
</style>