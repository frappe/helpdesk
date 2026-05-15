<template>
  <div class="flex flex-col gap-3 px-5 py-3 border-t bg-white">
    <!-- Subject -->
    <FormControl
      v-model="form.subject"
      :label="__('Subject')"
      type="text"
      size="sm"
      variant="subtle"
      :placeholder="__('Enter task subject')"
    />

    <div class="grid grid-cols-2 gap-3">
      <FormControl
        v-model="form.status"
        :label="__('Status')"
        type="select"
        size="sm"
        variant="subtle"
        :options="statusOptions"
      />
      <FormControl
        v-model="form.priority"
        :label="__('Priority')"
        type="select"
        size="sm"
        variant="subtle"
        :options="priorityOptions"
      />
    </div>

    <!-- Start + End date row -->
    <div class="grid grid-cols-2 gap-3">
      <FormControl
        v-model="form.expected_start_date"
        :label="__('Start Date')"
        type="date"
        size="sm"
        variant="subtle"
      />
      <FormControl
        v-model="form.expected_end_date"
        :label="__('End Date')"
        type="date"
        size="sm"
        variant="subtle"
      />
    </div>

    <div class="flex flex-col gap-1">
      <label class="block text-xs text-gray-600">{{ __("Description") }}</label>
      <TextEditor
        ref="editorRef"
        :editor-class="'prose-sm max-w-none min-h-[5rem] border rounded px-2 py-1.5'"
        :content="form.task_description"
        :editable="true"
        :starterkit-options="{ heading: { levels: [2, 3, 4, 5, 6] } }"
        :placeholder="__('Optional description')"
        @change="(v) => (form.task_description = v)"
      />
    </div>

    <div class="flex justify-end gap-2">
      <Button :label="__('Discard')" @click="handleDiscard" />
      <Button
        variant="solid"
        :label="__('Create Task')"
        :loading="loading"
        :disabled="isDisabled"
        @click="handleSubmit"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { isContentEmpty } from "@/utils";
import { Button, FormControl, TextEditor, call, toast } from "frappe-ui";
import { computed, ref } from "vue";

const props = defineProps({
  ticketId: {
    type: String,
    required: true,
  },
});

const emit = defineEmits(["submit", "discard"]);

const loading = ref(false);

const defaultForm = () => ({
  subject: "",
  status: "Open",
  priority: "Medium",
  task_description: "",
  expected_start_date: "",
  expected_end_date: "",
});

const form = ref(defaultForm());

const isDisabled = computed(() => !form.value.subject?.trim() || loading.value);

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

function handleDiscard() {
  form.value = defaultForm();
  emit("discard");
}

async function handleSubmit() {
  if (!form.value.subject?.trim()) {
    toast.error(__("Subject is required"));
    return;
  }

  // double-submit guard
  if (loading.value) return;
  loading.value = true;

  try {
    await call("helpdesk.helpdesk.doctype.hd_task.hd_task.create_task", {
      ticket: props.ticketId,
      subject: form.value.subject,
      status: form.value.status,
      priority: form.value.priority,
      task_description: isContentEmpty(form.value.task_description)
        ? null
        : form.value.task_description,
      expected_start_date: form.value.expected_start_date || null,
      expected_end_date: form.value.expected_end_date || null,
    });
    toast.success(__("Task created"));
    form.value = defaultForm();
    emit("submit");
  } catch (e: any) {
    toast.error(e?.message || __("Failed to create task"));
  } finally {
    loading.value = false;
  }
}

const editorRef = ref(null);

defineExpose({ editorRef });
</script>
