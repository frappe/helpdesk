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
      <div v-if="column.key === 'default_time'">
        <Checkbox v-model="props.row.default_time" />
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
            label: 'Duplicate',
            onClick: () => duplicate(),
            icon: 'copy',
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
      <h3 class="text-2xl font-semibold">Edit Status</h3>
    </template>
    <template #body-content>
      <div class="flex flex-col gap-4">
        <FormControl
          :type="'select'"
          size="sm"
          variant="subtle"
          placeholder="Select Status"
          label="Status"
          v-model="statusData.status"
          :options="[
            {
              label: 'Open',
              value: 'Open',
            },
            {
              label: 'Replied',
              value: 'Replied',
            },
            {
              label: 'Resolved',
              value: 'Resolved',
            },
            {
              label: 'Closed',
              value: 'Closed',
            },
          ]"
          required
        />
        <FormControl
          :type="'select'"
          size="sm"
          variant="subtle"
          placeholder="Select Status"
          label="SLA behavior"
          v-model="statusData.sla_behavior"
          :options="[
            {
              label: 'Fulfilled',
              value: 'Fulfilled',
            },
            {
              label: 'Paused',
              value: 'Paused',
            },
          ]"
          required
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
import { Button, Checkbox, Dropdown, FeatherIcon, Dialog } from "frappe-ui";

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
  statusList: {
    type: Array<any>,
    required: true,
  },
});

const dialog = ref(false);
const isConfirmingDelete = ref(false);
const statusData = ref({
  status: props.row.status,
  sla_behavior: props.row.sla_behavior,
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

  props.statusList.splice(props.statusList.indexOf(props.row), 1);
};

const duplicate = () => {
  console.log("duplicate");
};

const editSla = () => {
  statusData.value = {
    status: props.row.status,
    sla_behavior: props.row.sla_behavior,
  };
  dialog.value = true;
};

function onSave() {
  props.row.status = statusData.value.status;
  props.row.sla_behavior = statusData.value.sla_behavior;
  statusData.value = {
    status: "",
    sla_behavior: "",
  };
  dialog.value = false;
}

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
