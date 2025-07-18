<template>
  <Dialog
    v-model="dialog"
    :options="{
      title: 'Edit response and resolution',
    }"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <FormControl
          :type="'select'"
          size="sm"
          variant="subtle"
          placeholder="Select Priority"
          label="Priority"
          v-model="priorityData.priority"
          :options="priorityOptions"
          required
        />
        <div>
          <FormLabel label="Response time" required />
          <Popover class="mt-2">
            <template #target="{ togglePopover }" class="w-max">
              <div
                @click="togglePopover()"
                class="w-full bg-gray-100 rounded p-1.5 px-2 text-base text-gray-800"
              >
                <div v-if="priorityData.response_time">
                  {{ formatTimeHMS(priorityData.response_time) }}
                </div>
                <div v-else class="text-gray-500">Select time</div>
              </div>
            </template>
            <template #body>
              <div class="absolute bg-white top-2">
                <DurationPicker
                  v-model="priorityData.response_time"
                  :options="{ seconds: false }"
                />
              </div>
            </template>
          </Popover>
        </div>
        <div>
          <FormLabel label="Resolution time" required />
          <Popover class="mt-2">
            <template #target="{ togglePopover }" class="w-max">
              <div
                @click="togglePopover()"
                class="w-full bg-gray-100 rounded p-1.5 px-2 text-base text-gray-800"
              >
                <div v-if="priorityData.resolution_time">
                  {{ formatTimeHMS(priorityData.resolution_time) }}
                </div>
                <div v-else class="text-gray-500">Select time</div>
              </div>
            </template>
            <template #body>
              <div class="absolute bg-white top-2">
                <DurationPicker
                  v-model="priorityData.resolution_time"
                  :options="{ seconds: false }"
                />
              </div>
            </template>
          </Popover>
        </div>
        <Checkbox
          v-model="priorityData.default_priority"
          label="Set default priority"
        />
      </div>
    </template>
    <template #actions>
      <div class="flex justify-between">
        <div>
          <Button
            variant="subtle"
            :theme="isConfirmingDelete ? 'red' : 'gray'"
            :label="isConfirmingDelete ? 'Confirm Delete' : 'Delete'"
            @click="deleteItem"
            icon-left="trash-2"
          />
        </div>
        <div class="flex gap-2">
          <Button
            variant="subtle"
            theme="gray"
            @click="dialog = false"
            label="Cancel"
          />
          <Button variant="solid" @click="onSave" label="Save" />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import {
  Button,
  Checkbox,
  Dialog,
  FormControl,
  FormLabel,
  Popover,
  toast,
} from "frappe-ui";
import { inject, ref } from "vue";
import { formatTimeHMS } from "../utils";
import DurationPicker from "@/components/frappe-ui/DurationPicker.vue";
import { slaData } from "@/stores/sla";

const dialog = defineModel<boolean>();
const emit = defineEmits(["onDefaultPriorityChange"]);
const isConfirmingDelete = ref(false);

const props = defineProps({
  row: {
    type: Object,
    required: true,
  },
});

const priorityOptions = inject("priorityOptions");

const priorityData = ref({
  priority: props.row.priority,
  resolution_time: props.row.resolution_time,
  response_time: props.row.response_time,
  default_priority: props.row.default_priority,
});

const validateForm = () => {
  if (!priorityData.value.priority) {
    toast.error("Please select a priority");
    return false;
  }

  const resolutionTime = parseInt(priorityData.value.resolution_time);
  if (isNaN(resolutionTime) || resolutionTime <= 0) {
    toast.error("Resolution time must be a positive number");
    return false;
  }

  const responseTime = parseInt(priorityData.value.response_time);
  if (isNaN(responseTime) || responseTime <= 0) {
    toast.error("Response time must be a positive number");
    return false;
  }

  if (priorityData.value.default_priority) {
    slaData.value.priorities.forEach((priority) => {
      priority.default_priority = false;
    });
  }

  return true;
};

const deleteItem = (event) => {
  event.preventDefault();
  if (!isConfirmingDelete.value) {
    isConfirmingDelete.value = true;
    return;
  }

  slaData.value.priorities.splice(
    slaData.value.priorities.indexOf(props.row),
    1
  );
};

const onSave = () => {
  if (!validateForm()) return;
  props.row.priority = priorityData.value.priority;
  props.row.resolution_time = priorityData.value.resolution_time;
  props.row.response_time = priorityData.value.response_time;
  props.row.default_priority = priorityData.value.default_priority;

  dialog.value = false;
};
</script>
