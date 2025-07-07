<template>
  <div
    class="grid gap-2 px-2 items-center"
    :style="{
      gridTemplateColumns: getGridTemplateColumnsForTable(props.columns),
    }"
  >
    <div
      v-for="column in props.columns"
      :key="column.key"
      class="w-full py-2 overflow-hidden whitespace-nowrap text-ellipsis"
    >
      <div v-if="column.key === 'default_priority'">
        <Checkbox
          v-model="props.row.default_priority"
          @update:modelValue="(e) => onDefaultPriorityChange(e)"
        />
      </div>
      <div
        v-else-if="
          column.key === 'response_time' || column.key === 'resolution_time'
        "
      >
        <Popover>
          <template #target="{ togglePopover }">
            <div
              @click="togglePopover()"
              class="min-h-7 w-full cursor-pointer select-none leading-5 p-1 px-2 hover:bg-gray-200 rounded"
            >
              {{ formatTimeHMS(props.row[column.key]) }}
            </div>
          </template>
          <template #body>
            <div class="absolute bg-white top-2">
              <DurationPicker v-model="props.row[column.key]" />
            </div>
          </template>
        </Popover>
      </div>
      <div v-else>
        <Select
          class="w-full bg-transparent cursor-pointer border-0 focus-visible:!ring-0 bg-none"
          :options="priorityOptions"
          v-model="props.row[column.key]"
        />
      </div>
    </div>
    <div class="flex justify-end">
      <Dropdown
        placement="right"
        :options="[
          {
            label: 'Edit',
            onClick: () => editItem(),
            icon: 'edit',
          },
          {
            label: 'Confirm Delete',
            component: (props) =>
              TemplateOption({
                option: isConfirmingDelete ? 'Confirm Delete' : 'Delete',
                icon: 'trash-2',
                active: props.active,
                variant: isConfirmingDelete ? 'danger' : 'gray',
                onClick: (event) => deleteItem(event),
              }),
          },
        ]"
      >
        <Button
          icon="more-horizontal"
          variant="ghost"
          @click="isConfirmingDelete = false"
        />
      </Dropdown>
    </div>
  </div>
  <hr class="my-0.5" v-if="!props.isLast" />
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
          @update:modelValue="onDefaultPriorityChange"
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
import { ref } from "vue";
import {
  Button,
  Checkbox,
  Dropdown,
  Dialog,
  toast,
  Select,
  Popover,
  FormLabel,
} from "frappe-ui";
import DurationPicker from "@/components/frappe-ui/DurationPicker.vue";
import { getGridTemplateColumnsForTable, TemplateOption } from "@/utils";

const props = defineProps({
  columns: {
    type: Array<any>,
    required: true,
  },
  row: {
    type: Object,
    required: true,
  },
  isLast: {
    type: Boolean,
    default: false,
  },
  priorityList: {
    type: Object,
    required: true,
  },
  priorityOptions: {
    type: Array<any>,
    required: true,
  },
});

const isConfirmingDelete = ref(false);
const dialog = ref(false);
const priorityData = ref({
  priority: props.row.priority,
  resolution_time: props.row.resolution_time,
  response_time: props.row.response_time,
  default_priority: props.row.default_priority,
});

const deleteItem = (event) => {
  event.preventDefault();
  if (!isConfirmingDelete.value) {
    isConfirmingDelete.value = true;
    return;
  }

  props.priorityList.splice(props.priorityList.indexOf(props.row), 1);
};

const editItem = () => {
  dialog.value = true;
  priorityData.value = {
    priority: props.row.priority,
    resolution_time: props.row.resolution_time,
    response_time: props.row.response_time,
    default_priority: props.row.default_priority,
  };
};

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
    props.priorityList.forEach((priority) => {
      priority.default_priority = false;
    });
  }

  return true;
};

const onSave = () => {
  if (!validateForm()) return;
  console.log("priorityData.value", priorityData.value);
  props.row.priority = priorityData.value.priority;
  props.row.resolution_time = priorityData.value.resolution_time;
  props.row.response_time = priorityData.value.response_time;
  props.row.default_priority = priorityData.value.default_priority;

  priorityData.value = {
    priority: "",
    resolution_time: "",
    response_time: "",
    default_priority: false,
  };

  dialog.value = false;
};

const onDefaultPriorityChange = (defaultPriority) => {
  props.priorityList.forEach((priority) => {
    priority.default_priority = false;
  });
  props.row.default_priority = defaultPriority;
};

function formatTimeHMS(seconds) {
  const days = Math.floor(seconds / (3600 * 24));
  const hours = Math.floor((seconds % (3600 * 24)) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainingSeconds = Math.floor(seconds % 60);

  let formattedTime = "";

  if (days > 0) {
    formattedTime += `${days} days `;
  }

  if (hours > 0) {
    formattedTime += `${hours} hours `;
  }

  if (minutes > 0) {
    formattedTime += `${minutes} minutes `;
  }

  if (remainingSeconds > 0) {
    formattedTime += `${remainingSeconds} seconds`;
  }

  return formattedTime.trim();
}
</script>
