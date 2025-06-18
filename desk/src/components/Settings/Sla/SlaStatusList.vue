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
    <SlaStatusListItem
      v-for="(row, index) in statusList"
      :key="row.name"
      :row="row"
      :columns="columns"
      :isLast="index === statusList.length - 1"
      :statusList="statusList"
    />
    <div v-if="statusList?.length === 0" class="text-center p-4 text-gray-600">
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
import { Button } from "frappe-ui";
import { createResource } from "frappe-ui";
import { activeScreen } from "./sla";
import SlaStatusListItem from "./SlaStatusListItem.vue";
import Draggable from "vuedraggable";
import NestedPopover from "@/components/NestedPopover.vue";
import Autocomplete from "@/components/frappe-ui/Autocomplete.vue";
import { computed, ref } from "vue";

const props = defineProps({
  statusList: {
    type: Array<any>,
    required: true,
  },
});

const dialog = ref(false);
const statusData = ref({
  status: "",
  sla_behavior: "",
});

function onSave() {
  props.statusList.push(statusData.value);
  dialog.value = false;
  statusData.value = {
    status: "",
    sla_behavior: "",
  };
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
const columns = [
  {
    label: "Status",
    key: "status",
  },
  {
    label: "SLA behavior",
    key: "sla_behavior",
  },
];
</script>
