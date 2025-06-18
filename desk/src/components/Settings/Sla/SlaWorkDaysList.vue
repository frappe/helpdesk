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
    <SlaWorkDaysListItem
      v-for="(row, index) in workDaysList"
      :key="row.name"
      :row="row"
      :columns="columns"
      :isLast="index === workDaysList.length - 1"
      :workDaysList="workDaysList"
    />
  </div>
</template>

<script setup lang="ts">
import { Button } from "frappe-ui";
import Draggable from "vuedraggable";
import NestedPopover from "@/components/NestedPopover.vue";
import Autocomplete from "@/components/frappe-ui/Autocomplete.vue";
import { computed, ref } from "vue";
import SlaWorkDaysListItem from "./SlaWorkDaysListItem.vue";

const dialog = ref(false);

const props = defineProps({
  workDaysList: {
    type: Array<any>,
    required: true,
  },
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
    label: "Day",
    key: "workday",
  },
  {
    label: "Holiday",
    key: "is_holiday",
  },
  {
    label: "Open time",
    key: "start_time",
  },
  {
    label: "Close time",
    key: "end_time",
  },
];
</script>
