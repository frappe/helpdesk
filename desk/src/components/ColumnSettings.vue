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
              <ColumnItem :column="element" @remove="removeColumn" />
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
          </div>
        </div>
      </div>
    </template>
  </NestedPopover>
</template>

<script setup lang="ts">
import { ref } from "vue";
import ColumnsIcon from "@/components/icons/ColumnsIcon.vue";
import ColumnItem from "@/components/ColumnItem.vue";
import NestedPopover from "@/components/NestedPopover.vue";
import { Autocomplete } from "frappe-ui";
import Draggable from "vuedraggable";

let emit = defineEmits(["event:column"]);
let edit = ref(false);

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
  let columnEvent = {
    event: "update",
    data: props.columns,
  };
  emit("event:column", columnEvent);
}

function removeColumn(c) {
  if (c.key === "name" || c.key === "_assign") {
    return;
    // TODO
  }
  let columnEvent = {
    event: "remove",
    data: c,
  };
  emit("event:column", columnEvent);
}
</script>
