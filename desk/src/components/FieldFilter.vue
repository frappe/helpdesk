<template>
  <div class="flex flex-wrap items-center gap-2">
    <div
      v-for="f in storage"
      :key="f.field.fieldname"
      class="flex items-center text-base"
    >
      <div class="rounded-l border-y border-l px-2 py-1.5 text-gray-800">
        {{ f.field.label }}
      </div>
      <Dropdown :options="getOperators(f)">
        <div class="cursor-pointer border-y px-2 py-1.5 text-gray-700">
          {{ f.operator }}
        </div>
      </Dropdown>
      <component :is="getValSelect(f)" class="border" />
      <div
        class="cursor-pointer rounded-r border-y border-r p-1.5 text-gray-800"
        @click="
          () => {
            storage.delete(f);
            apply();
          }
        "
      >
        <Icon icon="lucide:x" class="h-4 w-4" />
      </div>
    </div>
    <Dropdown :options="optionsField">
      <template #default>
        <Button
          :label="storage.size ? 'Add more' : 'Add filter'"
          theme="gray"
          variant="outline"
        >
          <template #prefix>
            <Icon
              :icon="storage.size ? 'lucide:plus' : 'lucide:list-filter'"
              class="h-4 w-4"
            />
          </template>
        </Button>
      </template>
    </Dropdown>
    <Button
      v-if="storage.size"
      label="Clear"
      theme="gray"
      variant="outline"
      @click="
        () => {
          storage.clear();
          apply();
        }
      "
    >
      <template #prefix>
        <Icon icon="lucide:x" class="h-4 w-4" />
      </template>
    </Button>
  </div>
</template>

<script setup lang="ts">
import { computed, h, watch } from "vue";
import { Button, Dropdown, FormControl } from "frappe-ui";
import { useDebounceFn } from "@vueuse/core";
import { Icon } from "@iconify/vue";
import { DocField, Filter } from "@/types";
import { useFilter } from "@/composables/filter";
import SearchComplete from "./SearchComplete.vue";

interface P {
  doctype: string;
  appendAssign?: boolean;
}

const props = withDefaults(defineProps<P>(), {
  appendAssign: false,
});

const { apply, fields, storage } = useFilter(props.doctype);
const typeCheck = ["Check"];
const typeLink = ["Link"];
const typeNumber = ["Float", "Int"];
const typeSelect = ["Select"];
const typeString = ["Data", "Long Text", "Small Text", "Text Editor", "Text"];

watch(
  storage,
  useDebounceFn(() => {
    if (storage.value.size) apply();
  }, 300),
  { deep: true }
);

const optionsField = computed(() =>
  fields
    .map((f) => ({
      label: f.label,
      onClick: () =>
        storage.value.add({
          field: f,
          fieldname: f.fieldname,
          operator: "is",
          value: getDefaultValue(f),
        }),
    }))
    .sort((a, b) => a.label.localeCompare(b.label))
);

function getOperators(f: Filter) {
  const fieldtype = f.field.fieldtype;
  let ops = [];
  if (typeString.includes(fieldtype) || typeNumber.includes(fieldtype)) {
    ops.push(...["equals", "not equals", "like", "not like"]);
  }
  if (typeNumber.includes(fieldtype)) {
    ops.push(...["<", ">", "<=", ">=", "equals", "not equals"]);
  }
  if (typeSelect.includes(fieldtype) || typeLink.includes(fieldtype)) {
    ops.push(...["is", "is not"]);
  }
  return ops.map((o) => ({
    label: o,
    onClick: () => (f.operator = o),
  }));
}

function getSelectOptions(f: DocField) {
  return f.options.split("\n");
}

function getDefaultValue(f: DocField) {
  if (typeSelect.includes(f.fieldtype)) {
    return getSelectOptions(f).slice(1).pop();
  }
  if (typeCheck.includes(f.fieldtype)) {
    return "Yes";
  }
  return "";
}

function getValSelect(f: Filter) {
  const fieldtype = f.field.fieldtype;
  const options = f.field.options;
  if (typeString.includes(fieldtype) || typeNumber.includes(fieldtype)) {
    return h(FormControl, {
      type: "text",
      class: "bg-gray-100",
      placeholder: f.value,
      onChange: (e) => (f.value = e.target.value),
    });
  }
  if (typeSelect.includes(fieldtype)) {
    return h(Dropdown, {
      options: getSelectOptions(f.field).map((o) => ({
        label: o,
        onClick: () => (f.value = o),
      })),
      button: {
        label: f.value,
      },
      class: "bg-gray-100",
    });
  }
  if (typeLink.includes(fieldtype)) {
    return h(SearchComplete, {
      value: f.value,
      doctype: options,
      class: "bg-gray-100",
      onChange: (v) => (f.value = v.value),
    });
  }
  if (typeCheck.includes(fieldtype)) {
    return h(Dropdown, {
      options: ["Yes", "No"].map((o) => ({
        label: o,
        onClick: () => (f.value = o),
      })),
      button: {
        label: f.value,
      },
      class: "bg-gray-100",
    });
  }
}
</script>
