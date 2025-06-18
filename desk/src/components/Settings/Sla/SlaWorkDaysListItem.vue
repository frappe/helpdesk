<template>
  <div
    class="grid gap-2 px-2 py-1 items-center"
    :style="{ gridTemplateColumns: getGridTemplateColumns(props.columns) }"
  >
    <div
      v-for="column in props.columns"
      :key="column.key"
      class="w-full py-2 overflow-hidden whitespace-nowrap text-ellipsis"
    >
      <div class="flex items-center" v-if="column.key === 'is_holiday'">
        <Switch
          size="sm"
          v-model="props.row.is_holiday"
          @update:modelValue="onHolidayChange(props.row, $event)"
        />
        <!-- <Checkbox v-model="props.row.is_holiday" /> -->
      </div>
      <div v-else-if="column.key === 'start_time' || column.key === 'end_time'">
        {{ formatTime(props.row[column.key]) }}
      </div>
      <div v-else>{{ props.row[column.key] }}</div>
    </div>
    <div class="flex justify-end">
      <Button variant="ghost" @click="editWorkDay">
        <template #icon>
          <EditIcon class="size-4" />
        </template>
      </Button>
    </div>
  </div>
  <hr class="my-0.5" v-if="!props.isLast" />
  <Dialog v-model="dialog">
    <template #body-title>
      <h3 class="text-2xl font-semibold">Edit Workday</h3>
    </template>
    <template #body-content>
      <div class="flex flex-col gap-4">
        <FormControl
          :type="'time'"
          size="sm"
          variant="subtle"
          placeholder="Start Time"
          label="Start Time"
          :value="formatTime(workDayData.start_time)"
          v-model="workDayData.start_time"
          required
        />
        <FormControl
          :type="'time'"
          size="sm"
          variant="subtle"
          placeholder="End Time"
          label="End Time"
          :value="formatTime(workDayData.end_time)"
          v-model="workDayData.end_time"
          required
        />
        <div class="flex items-center gap-2">
          <Switch v-model="workDayData.is_holiday" />
          <span class="text-sm"> Set as weekly holiday </span>
        </div>
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end">
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
import { Button, Checkbox, FeatherIcon, Dialog, Switch } from "frappe-ui";
import { EditIcon } from "@/components/icons";

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
  workDaysList: {
    type: Object,
    required: true,
  },
});

const isConfirmingDelete = ref(false);
const dialog = ref(false);
const workDayData = ref({
  workday: props.row.workday,
  is_holiday: props.row.is_holiday,
  start_time: props.row.start_time,
  end_time: props.row.end_time,
});

const editWorkDay = () => {
  dialog.value = true;
  workDayData.value = {
    workday: props.row.workday,
    is_holiday: props.row.is_holiday,
    start_time: props.row.start_time,
    end_time: props.row.end_time,
  };
};

const onSave = () => {
  const item = props.workDaysList.findIndex(
    (item) => item.workday === props.row.workday
  );
  if (item !== -1) {
    props.workDaysList[item].is_holiday = workDayData.value.is_holiday;
    props.workDaysList[item].start_time = workDayData.value.start_time;
    props.workDaysList[item].end_time = workDayData.value.end_time;
  }
  workDayData.value = {
    workday: "",
    is_holiday: false,
    start_time: "",
    end_time: "",
  };
  console.log("props.row", props.row);
  dialog.value = false;
};

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

const onHolidayChange = (row, value) => {
  console.log("value", value, row);
  row.is_holiday = value;
};

const formatTime = (time) => {
  if (!time) return "00:00";
  const [hours = "00", minutes = "00"] = time.split(":");
  return [hours.padStart(2, "0"), minutes.padStart(2, "0")].join(":");
};
</script>
