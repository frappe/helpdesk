<template>
  <NestedPopover>
    <template #target>
      <Button ref="sortButtonRef" label="Sort">
        <template #prefix><SortIcon class="h-4" /></template>
        <template v-if="sorts?.length" #suffix>
          <div
            class="text-2xs flex h-5 w-5 items-center justify-center rounded bg-gray-900 pt-[1px] font-medium text-white"
          >
            {{ sorts.length }}
          </div>
        </template>
      </Button>
    </template>
    <template #body="{ close }">
      <div class="my-2 rounded-lg border border-gray-100 bg-white shadow-xl">
        <div class="min-w-[352px] p-2">
          <div
            v-if="sorts?.length"
            id="sort-list"
            class="mb-3 flex flex-col gap-2"
          >
            <div
              v-for="(sort, i) in sorts"
              :key="sort.fieldname"
              class="flex items-center gap-2"
            >
              <Autocomplete
                class="!w-32"
                :value="sort.fieldname"
                :options="sortableFields"
                placeholder="Sort by"
                @change="(field) => updateSort(i, field)"
              />
              <FormControl
                class="!w-32"
                type="select"
                :value="sort.direction"
                :options="[
                  { label: 'Ascending', value: 'asc' },
                  { label: 'Descending', value: 'desc' },
                ]"
                placeholder="Sort by"
                @change="(e) => updateSort(i, null, e.target.value)"
              />
              <Button variant="ghost" icon="x" @click="removeSort(i)" />
            </div>
          </div>
          <div
            v-else
            class="mb-3 flex h-7 items-center px-3 text-sm text-gray-600"
          >
            Empty - Choose a field to sort by
          </div>
          <div class="flex items-center justify-between gap-2">
            <Autocomplete
              :options="sortableFields"
              value=""
              placeholder="Sort by"
              @change="(e) => setSort(e)"
            >
              <template #target="{ togglePopover }">
                <Button
                  class="!text-gray-600"
                  variant="ghost"
                  label="Add Sort"
                  @click="togglePopover()"
                >
                  <template #prefix>
                    <FeatherIcon name="plus" class="h-4" />
                  </template>
                </Button>
              </template>
            </Autocomplete>
            <Button
              v-if="sorts?.length"
              class="!text-gray-600"
              variant="ghost"
              label="Clear Sort"
              @click="clearSort(close)"
            />
          </div>
        </div>
      </div>
    </template>
  </NestedPopover>
</template>

<script setup lang="ts">
import { Autocomplete } from "frappe-ui";

import { NestedPopover } from "@/components";
import SortIcon from "@/components/icons/SortIcon.vue";

const props = defineProps({
  sortableFields: {
    type: Array,
    required: true,
  },
  sorts: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits(["event:sort"]);

function setSort(field) {
  emit("event:sort", {
    event: "add",
    data: {
      fieldname: field,
      direction: "asc",
      sortToApply: convertToString(
        props.sorts.concat([{ fieldname: field, direction: "asc" }])
      ),
    },
  });
}

function updateSort(index, field = null, direction = null) {
  if (!field) {
    field = props.sorts[index].fieldname;
  }

  if (!direction) {
    direction = "asc";
  }

  emit("event:sort", {
    event: "update",
    data: {
      index,
      fieldname: field,
      direction: direction,
      sortToApply: convertToString(
        props.sorts.map((f, i) => {
          if (i === index) {
            return { fieldname: field, direction: direction };
          }
          return f;
        })
      ),
    },
  });
}

function removeSort(index) {
  emit("event:sort", {
    event: "remove",
    data: {
      index,
      sortToApply: convertToString(props.sorts.filter((f, i) => i !== index)),
    },
  });
}

function clearSort(close: Function) {
  emit("event:sort", {
    event: "clear",
  });
  close();
}

function convertToString(values) {
  let _sortValues = "";
  values.forEach((f) => {
    _sortValues += `${f.fieldname.value} ${f.direction}, `;
  });
  _sortValues = _sortValues.slice(0, -2);
  return _sortValues;
}
</script>
