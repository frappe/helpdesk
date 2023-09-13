<template>
  <NestedPopover>
    <template #target>
      <Button label="Filters" theme="gray" variant="outline">
        <template #prefix>
          <LucideListFilter class="h-4 w-4" />
        </template>
        <template v-if="storage.size" #suffix>
          <Badge :label="storage.size" theme="gray" variant="subtle" />
        </template>
      </Button>
    </template>
    <template #body="{ close }">
      <div class="my-2 rounded bg-white shadow">
        <div class="min-w-[400px] p-2">
          <div
            v-for="(f, i) in storage"
            v-if="storage.size"
            id="filter-list"
            :key="i"
            class="mb-3 flex items-center justify-between gap-2"
          >
            <div class="flex items-center gap-2">
              <div class="w-13 pl-2 text-end text-base text-gray-600">
                {{ i == 0 ? "Where" : "And" }}
              </div>
              <div id="fieldname" class="!min-w-[140px]">
                <Autocomplete
                  :value="f.field.fieldname"
                  :options="fields"
                  placeholder="Filter by..."
                  @change="(e) => updateFilter(e, i)"
                />
              </div>
              <div id="operator">
                <FormControl
                  v-model="f.operator"
                  type="select"
                  :options="getOperators(f.field.fieldtype)"
                  placeholder="Operator"
                />
              </div>
              <div id="value" class="!min-w-[140px]">
                <SearchComplete
                  v-if="typeLink.includes(f.field.fieldtype)"
                  :doctype="f.field.options"
                  :value="f.value"
                  placeholder="Value"
                  @change="(v) => (f.value = v.value)"
                />
                <component
                  :is="getValSelect(f.field.fieldtype, f.field.options)"
                  v-else
                  v-model="f.value"
                  placeholder="Value"
                />
              </div>
            </div>
            <Button variant="ghost" icon="x" @click="removeFilter(i)" />
          </div>
          <div
            v-else
            class="mb-3 flex h-7 items-center px-3 text-sm text-gray-600"
          >
            Empty - Choose a field to filter by
          </div>
          <div class="flex items-center justify-between gap-2">
            <Autocomplete
              value=""
              :options="fields"
              placeholder="Filter by..."
              @change="(e) => setfilter(e)"
            >
              <template #target="{ togglePopover }">
                <Button
                  class="!text-gray-600"
                  variant="ghost"
                  label="Add filter"
                  @click="() => togglePopover()"
                >
                  <template #prefix>
                    <LucidePlus class="h-4 w-4" />
                  </template>
                </Button>
              </template>
            </Autocomplete>
            <Button
              v-if="storage.size"
              class="!text-gray-600"
              variant="ghost"
              label="Clear all filter"
              @click="() => clearfilter(close)"
            />
          </div>
        </div>
      </div>
    </template>
  </NestedPopover>
</template>
<script setup>
import { h, watch } from "vue";
import { Badge, Autocomplete, FormControl } from "frappe-ui";
import { useDebounceFn } from "@vueuse/core";
import { useFilter } from "@/composables/filter";
import { NestedPopover, SearchComplete } from "@/components";

const props = defineProps({
  doctype: {
    type: String,
    required: true,
  },
});

const { apply, fields, storage } = useFilter(props.doctype);
const typeCheck = ["Check"];
const typeLink = ["Link"];
const typeNumber = ["Float", "Int"];
const typeSelect = ["Select"];
const typeString = ["Data", "Long Text", "Small Text", "Text Editor", "Text"];

watch(
  storage,
  useDebounceFn(() => apply(), 300),
  { deep: true }
);

function getOperators(fieldtype) {
  let options = [];
  if (typeString.includes(fieldtype)) {
    options.push(
      ...[
        { label: "Equals", value: "equals" },
        { label: "Not Equals", value: "not equals" },
        { label: "Like", value: "like" },
        { label: "Not Like", value: "not like" },
      ]
    );
  }
  if (typeNumber.includes(fieldtype)) {
    options.push(
      ...[
        { label: "<", value: "<" },
        { label: ">", value: ">" },
        { label: "<=", value: "<=" },
        { label: ">=", value: ">=" },
        { label: "Equals", value: "equals" },
        { label: "Not Equals", value: "not equals" },
      ]
    );
  }
  if (typeSelect.includes(fieldtype) || typeLink.includes(fieldtype)) {
    options.push(
      ...[
        { label: "Is", value: "is" },
        { label: "Is Not", value: "is not" },
      ]
    );
  }
  if (typeCheck.includes(fieldtype)) {
    options.push(...[{ label: "Equals", value: "equals" }]);
  }
  return options;
}

function getValSelect(fieldtype, options) {
  if (typeSelect.includes(fieldtype) || typeCheck.includes(fieldtype)) {
    const _options =
      fieldtype == "Check" ? ["Yes", "No"] : getSelectOptions(options);
    return h(FormControl, {
      type: "select",
      options: _options.map((o) => ({
        label: o,
        value: o,
      })),
    });
  } else {
    return h(FormControl, { type: "text" });
  }
}

function getDefaultValue(field) {
  if (typeSelect.includes(field.fieldtype)) {
    return getSelectOptions(field.options)[0];
  }
  if (typeCheck.includes(field.fieldtype)) {
    return "Yes";
  }
  return "";
}

function getDefaultOperator(fieldtype) {
  if (typeSelect.includes(fieldtype) || typeLink.includes(fieldtype)) {
    return "is";
  }
  if (typeCheck.includes(fieldtype) || typeNumber.includes(fieldtype)) {
    return "equals";
  }
  return "like";
}

function getSelectOptions(options) {
  return options.split("\n");
}

function setfilter(data) {
  storage.value.add({
    field: {
      label: data.label,
      fieldname: data.value,
      fieldtype: data.fieldtype,
      options: data.options,
    },
    fieldname: data.value,
    operator: getDefaultOperator(data.fieldtype),
    value: getDefaultValue(data),
  });
}

function updateFilter(data, index) {
  storage.value.delete(Array.from(storage.value)[index]);
  storage.value.add({
    fieldname: data.value,
    operator: getDefaultOperator(data.fieldtype),
    value: getDefaultValue(data),
    field: {
      label: data.label,
      fieldname: data.value,
      fieldtype: data.fieldtype,
      options: data.options,
    },
  });
}

function removeFilter(index) {
  storage.value.delete(Array.from(storage.value)[index]);
}

function clearfilter(close) {
  storage.value.clear();
  close();
}
</script>
