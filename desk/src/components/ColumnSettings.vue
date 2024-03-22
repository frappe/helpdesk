<template>
  <NestedPopover>
    <template #target>
      <Button label="Columns">
        <template #prefix>
          <ColumnsIcon class="h-4" />
        </template>
      </Button>
    </template>
    <template #body>
      <div
        class="my-2 rounded-lg border border-gray-100 bg-white p-1.5 shadow-xl"
      >
        <div v-if="!edit">
          <Draggable
            :list="columns"
            item-key="key"
            class="list-group"
            @end="update"
          >
            <template #item="{ element }">
              <div
                class="flex cursor-grab items-center justify-between gap-6 rounded px-2 py-1.5 text-base text-gray-800 hover:bg-gray-100"
              >
                <div class="flex items-center gap-2">
                  <DragIcon class="h-3.5" />
                  <div>{{ element.label }}</div>
                </div>
                <div class="flex cursor-pointer items-center gap-1">
                  <Button
                    variant="ghost"
                    class="!h-5 w-5 !p-1"
                    @click="editColumn(element)"
                  >
                    <EditIcon class="h-3.5" />
                  </Button>
                  <Button
                    variant="ghost"
                    class="!h-5 w-5 !p-1"
                    @click="removeColumn(element)"
                  >
                    <FeatherIcon name="x" class="h-3.5" />
                  </Button>
                </div>
              </div>
            </template>
          </Draggable>
          <div class="mt-1.5 flex flex-col gap-1 border-t pt-1.5">
            <Autocomplete
              value=""
              :options="fields"
              @change="(e) => addColumn(e)"
            >
              <template #target="{ togglePopover }">
                <Button
                  class="w-full !justify-start !text-gray-600"
                  variant="ghost"
                  label="Add Column"
                  @click="togglePopover()"
                >
                  <template #prefix>
                    <FeatherIcon name="plus" class="h-4" />
                  </template>
                </Button>
              </template>
            </Autocomplete>
            <Button
              class="w-full !justify-start !text-gray-600"
              variant="ghost"
              label="Reset to Default"
              @click="resetToDefault(close)"
            >
              <template #prefix>
                <ReloadIcon class="h-4" />
              </template>
            </Button>
          </div>
        </div>
        <div v-else>
          <div
            class="flex flex-col items-center justify-between gap-2 rounded px-2 py-1.5 text-base text-gray-800"
          >
            <div class="flex flex-col items-center gap-3">
              <FormControl
                v-model="column.label"
                type="text"
                size="md"
                label="Label"
                class="w-full"
                placeholder="Column Label"
              />
              <FormControl
                v-model="column.width"
                type="text"
                size="md"
                label="Width"
                class="w-full"
                placeholder="Column Width"
                description="Width can be in number, pixel or rem (eg. 3, 30px, 10rem)"
                :debounce="500"
              />
            </div>
            <div class="flex w-full gap-2 border-t pt-2">
              <Button
                variant="subtle"
                label="Cancel"
                class="w-full flex-1"
                @click="cancelUpdate"
              />
              <Button
                variant="solid"
                label="Update"
                class="w-full flex-1"
                @click="update"
              />
            </div>
          </div>
        </div>
      </div>
    </template>
  </NestedPopover>
</template>

<script setup lang="ts">
import { ref } from "vue";
import ColumnsIcon from "@/components/icons/ColumnsIcon.vue";
import EditIcon from "@/components/icons/EditIcon.vue";
import NestedPopover from "@/components/NestedPopover.vue";
import { Autocomplete } from "frappe-ui";
import Draggable from "vuedraggable";

let emit = defineEmits(["event:column"]);
let edit = ref(false);
const column = ref({
  old: {},
  label: "",
  key: "",
  width: "10rem",
});

let props = defineProps({
  fields: {
    type: Array,
    required: true,
  },
  columns: {
    type: Array,
    required: true,
  },
});

function resetToDefault(close) {
  let columnEvent = {
    event: "reset",
  };
  emit("event:column", columnEvent);
  close();
}

function editColumn(c) {
  edit.value = true;
  column.value = c;
  column.value.old = { ...c };
}

function cancelUpdate() {
  edit.value = false;
  column.value.label = column.value.old.label;
  column.value.width = column.value.old.width;
  delete column.value.old;
}

function addColumn(c) {
  let columnEvent = {
    event: "add",
    data: {
      label: c.label,
      type: c.type,
      key: c.value,
      width: "10rem",
    },
  };
  emit("event:column", columnEvent);
}

function update() {
  edit.value = false;
  let columnEvent = {
    event: "update",
  };
  emit("event:column", columnEvent);
}

function removeColumn(c) {
  let columnEvent = {
    event: "remove",
    data: c,
  };
  emit("event:column", columnEvent);
}
</script>
