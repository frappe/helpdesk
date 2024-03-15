<template>
  <NestedPopover>
    <template #target>
      <Button label="Filter">
        <template #prefix>
          <FilterIcon class="h-4" />
        </template>
        <template v-if="props.filters.length" #suffix>
          <div
            class="text-2xs flex h-5 w-5 items-center justify-center rounded bg-gray-900 pt-[1px] font-medium text-white"
          >
            {{ props.filters.length }}
          </div>
        </template>
      </Button>
    </template>
    <template #body="{ close }">
      <div class="my-2 rounded bg-white shadow">
        <div class="min-w-[400px] p-2">
          <div v-if="props.filters.length">
            <div
              v-for="(filter, idx) in props.filters"
              id="filter-list"
              :key="idx"
              class="mb-3 flex items-center justify-between gap-2"
            >
              <div class="flex items-center gap-2">
                <div class="w-13 pl-2 text-end text-base text-gray-600">
                  {{ idx == 0 ? "Where" : "And" }}
                </div>
                <div id="fieldname" class="!min-w-[140px]">
                  <Autocomplete
                    :value="filter.field.fieldname"
                    :options="props.filterableFields"
                    placeholder="Filter by..."
                    @change="(field) => updateFilter(idx, field)"
                  />
                </div>
                <div id="operator">
                  <FormControl
                    type="select"
                    :value="filter.operator"
                    :options="getOperators(filter.field.fieldtype)"
                    placeholder="Operator"
                    @change="
                      (e) => updateFilter(idx, null, null, e.target.value)
                    "
                  />
                </div>
                <div id="value" class="!min-w-[140px]">
                  <SearchComplete
                    v-if="typeLink.includes(filter.field.fieldtype)"
                    :key="filter.field.fieldname"
                    :doctype="filter.field.options"
                    :value="filter.value.toString()"
                    @change="(v) => updateFilter(idx, null, v.value)"
                  />
                  <component
                    :is="
                      getValSelect(filter.field.fieldtype, filter.field.options)
                    "
                    v-else
                    :value="filter.value"
                    placeholder="Value"
                    @change="(e) => updateFilter(idx, null, e.target.value)"
                  />
                </div>
              </div>
              <Button variant="ghost" icon="x" @click="removeFilter(idx)" />
            </div>
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
              :options="props.filterableFields"
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
              v-if="props.filters.length"
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

<script setup lang="ts">
import { h } from "vue";
import { Autocomplete, FormControl } from "frappe-ui";
import { NestedPopover, SearchComplete } from "@/components";
import FilterIcon from "@/components/icons/FilterIcon.vue";
import { DocField } from "@/types";

let emit = defineEmits(["event:filter"]);

const props = defineProps({
  filters: {
    type: Array,
    required: true,
  },
  filterableFields: {
    type: Array,
    required: true,
  },
});

function setfilter(data) {
  let filterEvent = {
    event: "add",
    data: {
      field: {
        fieldname: data.fieldname,
        fieldtype: data.fieldtype,
        label: data.label,
        name: data.value, //TODO: why is this value can i remove this?
        options: data.options,
      },
      operator: getDefaultOperator(data.fieldtype),
      value: getDefaultValue(data),
    },
  };
  filterEvent.data["filterToApply"] = getFilterToApply({
    fieldname: filterEvent.data.field.fieldname,
    operator: filterEvent.data.operator,
    value: filterEvent.data.value,
  });
  emit("event:filter", filterEvent);
}

function updateFilter(
  index: number,
  field = null,
  value: string = null,
  operator: string = null
) {
  let filter = JSON.parse(JSON.stringify(props.filters[index]));

  if (field) {
    filter["field"] = field;
  }

  if (value !== null) {
    filter["value"] = value;
  } else {
    filter["value"] = props.filters[index]["value"];
  }

  if (operator !== null) {
    filter["operator"] = operator;
  } else {
    filter["operator"] = props.filters[index]["operator"];
  }

  emit("event:filter", {
    event: "update",
    data: {
      index: index,
      filterToApply: getFilterToApply({
        fieldname: filter["field"].fieldname,
        operator: filter["operator"],
        value: filter["value"],
      }),
      field: filter["field"],
      operator: filter["operator"],
      value: filter["value"],
    },
  });
}

function clearfilter(close: Function) {
  emit("event:filter", {
    event: "clear",
  });
  close();
}

function removeFilter(index: number) {
  emit("event:filter", {
    event: "remove",
    index,
  });
}

function getFilterToApply(filter) {
  let filterToApply = {};
  let operator;

  const operatorMap = {
    is: "=",
    "is not": "!=",
    equals: "=",
    "not equals": "!=",
    yes: true,
    no: false,
    like: "LIKE",
    "not like": "NOT LIKE",
    ">": ">",
    "<": "<",
    ">=": ">=",
    "<=": "<=",
  };

  if (filter.fieldname === "_assign") {
    operator = filter.operator === "is" ? "LIKE" : "NOT LIKE";
  } else {
    operator = operatorMap[filter.operator.toLowerCase()];
  }

  let value = filter.value;

  if (
    ["LIKE", "NOT LIKE"].includes(operator) &&
    !(value.startsWith("%") || value.endsWith("%"))
  ) {
    value = `%${value}%`;
  }

  filterToApply[filter.fieldname] = [operator, value];
  return filterToApply;
}

const typeCheck = ["Check"];
const typeLink = ["Link"];
const typeNumber = ["Float", "Int"];
const typeSelect = ["Select"];
const typeString = ["Data", "Long Text", "Small Text", "Text Editor", "Text"];

function getOperators(fieldtype: string) {
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

function getValSelect(fieldtype: string, options: string) {
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

function getSelectOptions(options: string) {
  return options.split("\n");
}

function getDefaultOperator(fieldtype: string) {
  if (typeSelect.includes(fieldtype) || typeLink.includes(fieldtype)) {
    return "is";
  }
  if (typeCheck.includes(fieldtype) || typeNumber.includes(fieldtype)) {
    return "equals";
  }
  return "like";
}

function getDefaultValue(field: DocField) {
  if (typeSelect.includes(field.fieldtype)) {
    return getSelectOptions(field.options)[0];
  }
  if (typeCheck.includes(field.fieldtype)) {
    return "Yes";
  }
  return "";
}
</script>
