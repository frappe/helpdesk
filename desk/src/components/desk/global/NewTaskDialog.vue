<template>
  <Dialog v-model="show" :options="{ size: 'xl' }">
    <template #body-title>
      <div class="flex items-center justify-between w-full pr-8">
        <h3 class="text-xl font-semibold leading-6 text-ink-gray-9">
          {{ __("Create Task") }}
        </h3>
      </div>
    </template>

    <template #body-content>
      <div class="flex flex-col gap-5 mt-2">

        <div class="space-y-1.5">
          <div class="text-sm text-ink-gray-5 flex items-center gap-1">
            {{ __('Title') }} <span class="text-red-500">*</span>
          </div>
          <TextInput
            ref="titleRef"
            v-model="form.title"
            variant="subtle"
            class="w-full rounded-md"
            :placeholder="__('Enter task title')"
          />
        </div>

        <div class="space-y-1.5">
          <div class="text-sm text-ink-gray-5">{{ __("Description") }}</div>
          <TextEditor
            editor-class="!prose-sm max-w-full overflow-auto min-h-[180px] max-h-80 py-1.5 px-2 rounded-b border border-[--surface-gray-2] bg-surface-gray-2 placeholder-ink-gray-4 hover:border-outline-gray-modals hover:shadow-sm focus:bg-surface-white focus:border-outline-gray-4 focus:shadow-sm focus:ring-0 focus-visible:ring-2 focus-visible:ring-outline-gray-3 text-ink-gray-8 transition-colors -mt-0.5"
            :bubble-menu="false"
            :fixed-menu="true"
            :content="form.description"
            :placeholder="__('Enter task description...')"
            @change="(val) => (form.description = val)"
          />
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
      <div class="flex justify-end w-full pt-2">
        <Button
          :label="__('Create')"
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
  FeatherIcon,
  FormControl,
  TextEditor,
  TextInput,
  call,
  createResource,
  toast,
} from "frappe-ui";
import { __ } from "@/translation";
import { isContentEmpty } from "@/utils";

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  ticketId:   { type: [String, Number], default: "" },
});

const emit = defineEmits(["update:modelValue", "submit", "task-created"]);

const show = computed({
  get: () => props.modelValue,
  set: (value) => emit("update:modelValue", value),
});

const loading  = ref(false);
const titleRef = ref(null);

const defaultForm = () => ({
  title:       "",
  description: "",
  due_date:    "",
  status:      "Backlog",
  priority:    "Low",
  assigned:    "",
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
  onSuccess(data: any[]) {
    const currentUser: string = (window as any).frappe?.session?.user || "";
    if (currentUser && show.value) {
      const match = data.find((u: any) => u.name === currentUser);
      if (match) form.value.assigned = currentUser;
    }
  },
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

function handleAssigneeChange(option: any) {
  if (!option)                         form.value.assigned = "";
  else if (typeof option === "object") form.value.assigned = option.value || "";
  else                                 form.value.assigned = option;
}

watch(show, (val) => {
  if (val) {
    form.value = defaultForm();
    if (agentsList.data) {
      const currentUser: string = (window as any).frappe?.session?.user || "";
      const match = (agentsList.data as any[]).find((u: any) => u.name === currentUser);
      if (match) form.value.assigned = currentUser;
    } else {
      agentsList.fetch();
    }
    nextTick(() => setTimeout(() => (titleRef.value as any)?.el?.focus?.(), 100));
  }
});

const statusOptions = [
  { label: __("Backlog"),     value: "Backlog"     },
  { label: __("Todo"),        value: "Todo"        },
  { label: __("In Progress"), value: "In Progress" },
  { label: __("Done"),        value: "Done"        },
  { label: __("Canceled"),    value: "Canceled"    },
];

const priorityOptions = [
  { label: __("Low"),    value: "Low"    },
  { label: __("Medium"), value: "Medium" },
  { label: __("High"),   value: "High"   },
];

async function handleSubmit() {
  if (!form.value.title?.trim()) { toast.error(__("Title is required")); return; }
  if (loading.value) return;
  loading.value = true;

  try {
    const ticketId = String(props.ticketId || "").trim();
    const payload: any = {
      title:       form.value.title,
      description: isContentEmpty(form.value.description) ? null : form.value.description,
      due_date:    form.value.due_date || null,
      status:      form.value.status,
      priority:    form.value.priority,
      assigned:    form.value.assigned || null,
    };
    if (ticketId) payload.ticket = ticketId;

    const result = await call(
      "helpdesk.helpdesk.doctype.hd_task.hd_task.create_task",
      payload,
    );

    toast.success(__("Task created"));
    show.value = false;
    // Emit immediately — no delay needed
    emit("submit", result);
    emit("task-created", result);

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