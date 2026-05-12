<template>
  <div
    class="border flex-1 px-3 pt-2.5 mb-4 border-transparent bg-surface-white rounded-md shadow text-base leading-6"
  >
    <div class="flex items-center justify-between mb-2">
      <div class="flex items-center gap-2">
        <input
          type="checkbox"
          :checked="activity.is_completed"
          @change="toggleComplete"
          class="w-4 h-4 accent-green-600 cursor-pointer"
        />
        <div
          class="font-medium text-gray-900"
          :class="{ 'line-through text-gray-400': activity.is_completed }"
        >
          {{ activity.title }}
        </div>
      </div>

      <div class="flex items-center gap-1">
        <div
          class="text-xs px-2 py-1 rounded"
          :class="{
            'bg-red-100 text-red-700': activity.priority === 'High',
            'bg-yellow-100 text-yellow-700': activity.priority === 'Medium',
            'bg-green-100 text-green-700': activity.priority === 'Low',
          }"
        >
          {{ activity.priority }}
        </div>

        <Button variant="ghost" @click="emit('edit', activity)">
          <template #icon>
            <FeatherIcon name="edit-2" class="size-3.5 text-gray-500" />
          </template>
        </Button>

        <Button variant="ghost" @click="confirmDelete">
          <template #icon>
            <FeatherIcon name="trash-2" class="size-3.5 text-red-400" />
          </template>
        </Button>
      </div>
    </div>

    <div
      v-if="activity.description"
      class="text-sm text-gray-600 mb-3"
      v-html="activity.description"
    />

    <div class="flex items-center justify-between text-xs text-gray-500">
      <div v-if="activity.assigned_to">
        Assigned to: {{ activity.assigned_to }}
      </div>

      <div v-if="activity.due_date">Due: {{ activity.due_date }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { createResource, FeatherIcon, Button, toast } from "frappe-ui";
import { __ } from "@/translation";

const props = defineProps({
  activity: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(["edit", "update"]);

function toggleComplete() {
  createResource({
    url: "frappe.client.set_value",
    params: {
      doctype: "HD Task",
      name: props.activity.name,
      fieldname: "is_completed",
      value: props.activity.is_completed ? 0 : 1,
    },
    auto: true,
    onSuccess: () => {
      toast.success(
        props.activity.is_completed
          ? __("Task marked incomplete")
          : __("Task marked complete")
      );
      emit("update");
    },
  });
}

function confirmDelete() {
  if (!window.confirm(__("Delete this task?"))) return;
  createResource({
    url: "frappe.client.delete",
    params: {
      doctype: "HD Task",
      name: props.activity.name,
    },
    auto: true,
    onSuccess: () => {
      toast.success(__("Task deleted"));
      emit("update");
    },
    onError: () => {
      toast.error(__("Failed to delete task"));
    },
  });
}
</script>
