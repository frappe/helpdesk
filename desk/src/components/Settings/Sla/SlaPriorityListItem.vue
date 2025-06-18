<template>
  <div
    class="grid gap-2 px-2 items-center"
    :style="{ gridTemplateColumns: getGridTemplateColumns(props.columns) }"
  >
    <div
      v-for="column in props.columns"
      :key="column.key"
      class="w-full py-2 overflow-hidden whitespace-nowrap text-ellipsis"
    >
      <div v-if="column.key === 'default_priority'">
        <Checkbox
          v-model="props.row.default_priority"
          class="pointer-events-none"
        />
      </div>
      <div v-else-if="column.key === 'response_time'">
        {{ formatTimeHMS(props.row[column.key]) }}
      </div>
      <div v-else-if="column.key === 'resolution_time'">
        {{ formatTimeHMS(props.row[column.key]) }}
      </div>
      <div v-else>{{ props.row[column.key] }}</div>
    </div>
    <div class="flex justify-end">
      <Dropdown
        :options="[
          {
            label: 'Edit',
            onClick: () => editSla(),
            icon: 'edit',
          },
          {
            label: isConfirmingDelete ? 'Confirm Delete' : 'Delete',
            onClick: () => deleteSla(),
            icon: 'trash-2',
          },
        ]"
      >
        <Button icon="more-horizontal" variant="ghost" />
      </Dropdown>
    </div>
  </div>
  <hr class="my-0.5" v-if="!props.isLast" />
  <Dialog v-model="dialog">
    <template #body-title>
      <h3 class="text-2xl font-semibold">Edit Response & Resolution metric</h3>
    </template>
    <template #body-content>
      <div class="flex flex-col gap-4">
        <FormControl
          :type="'select'"
          size="sm"
          variant="subtle"
          placeholder="Select Priority"
          label="Priority"
          v-model="priorityData.priority"
          :options="[
            {
              label: 'Low',
              value: 'Low',
            },
            {
              label: 'Medium',
              value: 'Medium',
            },
            {
              label: 'High',
              value: 'High',
            },
          ]"
          required
        />
        <FormControl
          :type="'text'"
          size="sm"
          variant="subtle"
          placeholder="Resolution Time"
          label="Resolution Time"
          description="Enter time in seconds"
          v-model="priorityData.resolution_time"
          required
        />
        <FormControl
          :type="'text'"
          size="sm"
          variant="subtle"
          placeholder="Response Time"
          label="Response Time"
          description="Enter time in seconds"
          v-model="priorityData.response_time"
          required
        />
        <Checkbox
          v-model="priorityData.default_priority"
          label="Set default priority"
        />
      </div>
    </template>
    <template #actions>
      <div class="flex justify-between">
        <div>
          <Button variant="subtle" theme="red" label="Delete">
            <template #prefix>
              <FeatherIcon name="trash-2" class="size-4" />
            </template>
          </Button>
        </div>
        <div class="flex gap-2">
          <Button variant="subtle" theme="gray" @click="dialog = false">
            Cancel
          </Button>
          <Button variant="solid" @click="onSave"> Save </Button>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { h, ref } from "vue";
import {
  Button,
  Checkbox,
  Dropdown,
  FeatherIcon,
  Dialog,
  createResource,
  toast,
} from "frappe-ui";

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
});

const isConfirmingDelete = ref(false);
const dialog = ref(false);
const priorityData = ref({
  priority: props.row.priority,
  resolution_time: props.row.resolution_time,
  response_time: props.row.response_time,
  default_priority: props.row.default_priority,
});

const deleteSla = () => {
  event.preventDefault();
  if (!isConfirmingDelete.value) {
    isConfirmingDelete.value = true;
    setTimeout(() => {
      isConfirmingDelete.value = false;
    }, 3000);
    return;
  }

  props.priorityList.splice(props.priorityList.indexOf(props.row), 1);
};

const editSla = () => {
  dialog.value = true;
  priorityData.value = {
    priority: props.row.priority,
    resolution_time: props.row.resolution_time,
    response_time: props.row.response_time,
    default_priority: props.row.default_priority,
  };
};

const onSave = () => {
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
  console.log("props.row", props.row);
  dialog.value = false;
};

function formatTimeHMS(seconds) {
  const days = Math.floor(seconds / (3600 * 24));
  const hours = Math.floor((seconds % (3600 * 24)) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainingSeconds = Math.floor(seconds % 60);

  let formattedTime = "";

  if (days > 0) {
    formattedTime += `${days}d `;
  }

  if (hours > 0) {
    formattedTime += `${hours}h `;
  }

  if (minutes > 0) {
    formattedTime += `${minutes}m `;
  }

  if (remainingSeconds > 0) {
    formattedTime += `${remainingSeconds}s`;
  }

  return formattedTime.trim();
}

function getGridTemplateColumns(columns) {
  let columnsWidth = columns
    .map((col) => {
      let width = col.width || 1;
      if (typeof width === "number") {
        return width + "fr";
      }
      return width;
    })
    .join(" ");
  return columnsWidth + " 22px";
}
</script>
