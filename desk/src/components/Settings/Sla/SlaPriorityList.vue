<template>
  <div class="rounded-md border p-1 border-gray-300 text-sm">
    <div
      class="grid px-2 items-center"
      :style="{
        gridTemplateColumns: getGridTemplateColumns(columns),
      }"
    >
      <div
        v-for="column in columns"
        :key="column.key"
        class="text-gray-600 overflow-hidden whitespace-nowrap text-ellipsis"
      >
        {{ column.label }}
      </div>
      <div class="flex justify-end">
        <NestedPopover>
          <template #target>
            <Button variant="ghost">
              <FeatherIcon name="columns" class="h-4" />
            </Button>
          </template>
          <template #body="{ close }">
            <div
              class="my-2 p-1 min-w-40 rounded-lg bg-surface-modal shadow-2xl ring-1 ring-black ring-opacity-5 focus:outline-none"
            >
              <div>
                <Draggable :list="columns" item-key="key" class="list-group">
                  <template #item="{ element }">
                    <div
                      class="flex cursor-grab items-center justify-between gap-6 rounded px-2 py-1.5 text-base text-ink-gray-8 hover:bg-surface-gray-2"
                    >
                      <div class="flex items-center gap-2">
                        <DragIcon class="h-3.5" />
                        <div>{{ element.label }}</div>
                      </div>
                      <div class="flex cursor-pointer items-center gap-1">
                        <!-- <Button variant="ghost" class="!h-5 w-5 !p-1">
                          <EditIcon class="h-3.5" />
                        </Button> -->
                        <Button variant="ghost" class="!h-5 w-5 !p-1">
                          <FeatherIcon name="x" class="h-3.5" />
                        </Button>
                      </div>
                    </div>
                  </template>
                </Draggable>
                <div
                  class="mt-1.5 flex flex-col gap-1 border-t border-outline-gray-modals pt-1.5"
                >
                  <Autocomplete value="">
                    <template #target="{ togglePopover }">
                      <Button
                        class="w-full !justify-start !text-ink-gray-5"
                        variant="ghost"
                        @click="togglePopover()"
                        label="Add Column"
                      >
                        <template #prefix>
                          <FeatherIcon name="plus" class="h-4" />
                        </template>
                      </Button>
                    </template>
                  </Autocomplete>
                  <Button
                    class="w-full !justify-start !text-ink-gray-5"
                    variant="ghost"
                    label="Reset to Default"
                  >
                    <template #prefix>
                      <ReloadIcon class="h-4" />
                    </template>
                  </Button>
                </div>
              </div>
            </div>
          </template>
        </NestedPopover>
      </div>
    </div>
    <hr class="my-0.5" />
    <SlaPriorityListItem
      v-for="(row, index) in props.priorityList"
      :key="row.name"
      :row="row"
      :columns="columns"
      :isLast="index === props.priorityList.length - 1"
      :priorityList="props.priorityList"
    />
    <div
      v-if="props.priorityList?.length === 0"
      class="text-center p-4 text-gray-600"
    >
      No items in the list
    </div>
  </div>
  <Button variant="subtle" label="Add row" class="mt-4" @click="dialog = true">
    <template #prefix>
      <FeatherIcon name="plus" class="h-4" />
    </template>
  </Button>
  <Dialog v-model="dialog">
    <template #body-title>
      <h3 class="text-2xl font-semibold">New row</h3>
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
import { Button } from "frappe-ui";
import SlaPriorityListItem from "./SlaPriorityListItem.vue";
import Draggable from "vuedraggable";
import NestedPopover from "@/components/NestedPopover.vue";
import Autocomplete from "@/components/frappe-ui/Autocomplete.vue";
import NewPriorityModal from "./NewPriorityModal.vue";
import { ref } from "vue";

const dialog = ref(false);

const props = defineProps({
  priorityList: {
    type: Array<any>,
    required: true,
  },
});

const priorityData = ref({
  priority: "",
  resolution_time: "",
  response_time: "",
  default_priority: false,
});

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

const columns = [
  {
    label: "Priority",
    key: "priority",
  },
  {
    label: "Default priority",
    key: "default_priority",
  },
  {
    label: "First response time",
    key: "response_time",
  },
  {
    label: "Resolution time",
    key: "resolution_time",
  },
];

function onSave() {
  dialog.value = false;
  props.priorityList.push(priorityData.value);
  priorityData.value = {
    priority: "",
    resolution_time: "",
    response_time: "",
    default_priority: false,
  };
}
</script>
