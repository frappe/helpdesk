<template>
  <div class="flex gap-2">
    <div
      v-for="f in storage"
      :key="f.field.fieldname"
      class="flex items-center space-x-1 text-base"
    >
      <div class="rounded-l bg-gray-100 px-2 py-1.5 text-gray-900">
        {{ f.field.label }}
      </div>
      <Dropdown :options="getOperators(f)">
        <div class="cursor-pointer bg-gray-100 px-2 py-1.5 text-gray-700">
          {{ f.operator }}
        </div>
      </Dropdown>
      <component :is="getValSelect(f)" />
      <div
        class="cursor-pointer rounded-r bg-gray-100 p-1.5 text-gray-800"
        @click="storage.delete(f)"
      >
        <Icon icon="lucide:x" class="h-4 w-4" />
      </div>
    </div>
    <Dropdown :options="optionsField">
      <template #default>
        <Button theme="gray" variant="subtle">
          <template #icon>
            <Icon icon="lucide:plus" />
          </template>
        </Button>
      </template>
    </Dropdown>
    <Button v-if="storage.size" theme="gray" variant="subtle">
      <template #icon>
        <Icon icon="lucide:check" />
      </template>
    </Button>
  </div>
</template>

<script setup lang="ts">
import { computed, h, ref, toRef } from "vue";
import { createResource, Button, Dropdown, FormControl } from "frappe-ui";
import { Icon } from "@iconify/vue";
import { DocField, Filter, Resource } from "@/types";
import SearchComplete from "./SearchComplete.vue";

interface P {
  doctype: string;
}

const props = defineProps<P>();
const doctype = toRef(props, "doctype");
const storage = ref(new Set<Filter>());

const typeCheck = ["Check"];
const typeLink = ["Link"];
const typeNumber = ["Float", "Int"];
const typeSelect = ["Select"];
const typeString = ["Data", "Long Text", "Small Text", "Text Editor", "Text"];

const fields: Resource<Array<DocField>> = createResource({
  url: "helpdesk.api.doc.get_filterable_fields",
  makeParams: () => ({
    doctype: doctype.value,
  }),
  auto: true,
});

const optionsField = computed(() =>
  fields.data?.map((f) => ({
    label: f.label,
    onClick: () =>
      storage.value.add({
        field: f,
        operator: "Equals",
        value: getDefaultValue(f),
      }),
  }))
);

function getOperators(f: Filter) {
  const fieldtype = f.field.fieldtype;
  let ops = [];
  if (typeString.includes(fieldtype) || typeNumber.includes(fieldtype)) {
    ops.push(...["Equals", "Not equals", "Like", "Not like"]);
  }
  if (typeNumber.includes(fieldtype)) {
    ops.push(...["<", ">", "<=", ">=", "Equals", "Not equals"]);
  }
  if (typeSelect.includes(fieldtype) || typeLink.includes(fieldtype)) {
    ops.push(...["Is", "Is not"]);
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
      onInput: (e) => (f.value = e.target.value),
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
