<template>
  <Dialog
    v-model="showDialog"
    :options="{ title: isEditing ? __('Edit Task') : __('New Task') }"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <!-- TITLE -->
        <FormControl
          v-model="form.title"
          :label="__('Title')"
          type="text"
          :placeholder="__('Enter task title')"
        />

        <!-- DATE + PRIORITY -->
        <div class="grid grid-cols-2 gap-3">
          <FormControl
            v-model="form.due_date"
            :label="__('Due Date')"
            type="date"
          />

          <FormControl
            v-model="form.priority"
            :label="__('Priority')"
            type="select"
            :options="[
              { label: __('Low'), value: 'Low' },
              { label: __('Medium'), value: 'Medium' },
              { label: __('High'), value: 'High' },
            ]"
          />
        </div>

        <!-- DESCRIPTION -->
        <div class="flex flex-col gap-1">
          <label class="block text-sm text-gray-600">
            {{ __("Description") }}
          </label>
          <textarea
            v-model="form.description"
            class="w-full rounded border border-gray-300 px-3 py-2 text-sm"
            rows="4"
          />
        </div>
      </div>
    </template>

    <template #actions>
      <Button
        class="w-full"
        variant="solid"
        :label="isEditing ? __('Update Task') : __('Create Task')"
        :loading="loading"
        @click="handleSave"
      />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from "vue";
import { Dialog, FormControl, Button, toast, createResource } from "frappe-ui";
import { __ } from "@/translation";

const props = defineProps({
  ticketId: {
    type: String,
    required: true,
  },
  task: {
    type: Object,
    default: null,
  },
});

const emit = defineEmits(["update"]);

const showDialog = defineModel<boolean>();

const loading = ref(false);

const isEditing = computed(() => !!props.task?.name);

const defaultForm = () => ({
  title: "",
  description: "",
  due_date: "",
  priority: "Medium",
});

const form = ref(defaultForm());

watch(
  () => props.task,
  (task) => {
    if (task) {
      form.value = {
        title: task.title || "",
        description: task.description || "",
        due_date: task.due_date || "",
        priority: task.priority || "Medium",
      };
    } else {
      form.value = defaultForm();
    }
  },
  { immediate: true }
);

watch(showDialog, (val) => {
  if (!val) {
    form.value = defaultForm();
  }
});

const createTask = createResource({
  url: "frappe.client.insert",
  onSuccess() {
    toast.success(__("Task created"));
    emit("update");
    showDialog.value = false;
    loading.value = false;
  },
  onError(error: any) {
    toast.error(error?.message || __("Failed to create task"));
    loading.value = false;
  },
});

const updateTask = createResource({
  url: "frappe.client.set_value",
  onSuccess() {
    toast.success(__("Task updated"));
    emit("update");
    showDialog.value = false;
    loading.value = false;
  },
  onError(error: any) {
    toast.error(error?.message || __("Failed to update task"));
    loading.value = false;
  },
});

function handleSave() {
  if (!form.value.title?.trim()) {
    toast.error(__("Title is required"));
    return;
  }

  loading.value = true;

  if (isEditing.value) {
    // Use set_value to avoid TimestampMismatchError — updates fields
    // directly without requiring the latest modified timestamp
    updateTask.submit({
      doctype: "HD Task",
      name: props.task.name,
      fieldname: {
        title: form.value.title,
        description: form.value.description || "",
        due_date: form.value.due_date || null,
        priority: form.value.priority || "Medium",
      },
    });
    return;
  }

  createTask.submit({
    doc: {
      doctype: "HD Task",
      reference_ticket: props.ticketId,
      title: form.value.title,
      description: form.value.description || "",
      due_date: form.value.due_date || null,
      priority: form.value.priority || "Medium",
      is_completed: 0,
    },
  });
}
</script>
