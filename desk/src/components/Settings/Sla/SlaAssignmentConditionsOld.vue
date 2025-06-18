<template>
  <div class="my-2 rounded-lg border border-gray-300 bg-white">
    <div class="min-w-72 p-2 sm:min-w-[400px]">
      <div
        v-if="filters?.size"
        v-for="(f, i) in filters"
        :key="i"
        id="filter-list"
        class="mb-4 sm:mb-3"
      >
        <div class="flex items-center justify-between gap-2">
          <div class="flex items-center gap-2">
            <div class="w-13 pl-2 text-end text-base text-gray-600">
              {{ i == 0 ? "Where" : "And" }}
            </div>
            <div id="fieldname" class="!min-w-[140px]">
              <AutocompleteNew
                :value="f.field.fieldname"
                :options="filterableFields.data"
                @change="(e) => updateFilter(e, i)"
                :placeholder="'First Name'"
              />
            </div>
            <div id="operator">
              <FormControl
                type="select"
                v-model="f.operator"
                @change="(e) => updateOperator(e, f)"
                :options="getOperators(f.field.fieldtype, f.field.fieldname)"
                :placeholder="'Equals'"
              />
            </div>
            <div id="value" class="!min-w-[140px]">
              <component
                :is="getValueControl(f)"
                v-model="f.value"
                @change="(v) => updateValue(v, f)"
                :placeholder="'John Doe'"
              />
            </div>
          </div>
          <Button
            class="flex"
            variant="ghost"
            icon="x"
            @click="removeFilter(i)"
          />
        </div>
      </div>
      <div v-else class="flex h-7 items-center px-3 text-sm text-gray-600">
        {{ "Empty - Add a condition" }}
      </div>
      <div class="flex items-center justify-between gap-2"></div>
    </div>
  </div>
  <Dropdown
    v-slot="{ open }"
    :options="[
      {
        label: 'Add condition',
        onClick: () => {
          setFilter(filterableFields.data[0]);
        },
      },
      {
        label: 'Add condition group',
        onClick: () => {},
      },
    ]"
  >
    <Button>
      Add condition
      <template #suffix>
        <FeatherIcon :name="open ? 'chevron-up' : 'chevron-down'" class="h-4" />
      </template>
    </Button>
  </Dropdown>
</template>
<script setup lang="ts">
import { h, computed, inject, reactive, ref } from "vue";
import {
  FormControl,
  Tooltip,
  DatePicker,
  DateTimePicker,
  DateRangePicker,
  NestedPopover,
  createResource,
  Popover,
} from "frappe-ui";
import { AutocompleteNew, Link, StarRating } from "@/components";
import { useScreenSize } from "@/composables/screen";
import FilterIcon from "@/components/icons/FilterIcon.vue";
import { useRoute } from "vue-router";

const props = defineProps({
  default_filters: {
    type: Object,
    required: false,
    default: {},
  },
});

const { isMobileView } = useScreenSize();

const typeCheck = ["Check"];
const typeLink = ["Link", "Dynamic Link"];
const typeNumber = ["Float", "Int", "Currency", "Percent"];
const typeSelect = ["Select"];
const typeString = ["Data", "Long Text", "Small Text", "Text Editor", "Text"];
const typeDate = ["Date", "Datetime"];
const typeRating = ["Rating"];

const route = useRoute();
const columns = ref([]);

const defaultOptions = reactive({
  doctype: "HD Ticket",
  hideViewControls: false,
  selectable: false,
  view: {
    view_type: "list",
    group_by_field: "owner",
    name: route.query.view,
  },
  groupByActions: [],
  default_page_length: 20,
  isCustomerPortal: false,
  hideColumnSetting: true,
  rowRoute: {
    name: "",
    prop: "",
  },
  // selectBannerActions: [
  //   {
  //     label: "Delete",
  //     icon: "trash-2",
  //     onClick: (selections: Set<string>) => {
  //       $dialog({
  //         title: "Delete",
  //         message: `Are you sure you want to delete ${selections.size} item(s)?`,
  //         actions: [
  //           {
  //             label: "Confirm",
  //             variant: "solid",
  //             onClick({ close }) {
  //               handleBulkDelete(close, selections);
  //             },
  //           },
  //         ],
  //       });
  //     },
  //     condition: () => !options.value.isCustomerPortal && isManager,
  //   },
  // ],
});

const options = computed(() => {
  return {
    ...defaultOptions,
    // ...props.options,
  };
});

const defaultParams = reactive({
  doctype: options.value.doctype,
  filters: {},
  default_filters: props.default_filters,
  order_by: "modified desc",
  page_length: options.value.default_page_length,
  page_length_count: options.value.default_page_length,
  view: options.value.view,
  columns: [],
  rows: [],
  show_customer_portal_fields: options.value.isCustomerPortal,
  is_default: false,
});

function handleFetchFromField(column) {
  if (!column.hasOwnProperty("key")) return column;
  const regex = /([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)/;
  const isFetchFromField = column.key.match(regex);
  column.key = isFetchFromField ? isFetchFromField[2] : column.key;
}

// function handleColumnConfig(column) {
//   if (!options.value?.columnConfig) return column;
//   const columnConfig = options.value.columnConfig;
//   if (!columnConfig.hasOwnProperty(column.key)) return column;
//   column.prefix = columnConfig[column.key]?.prefix;

//   return column;
// }

const list = createResource({
  url: "helpdesk.api.doc.get_list_data",
  params: defaultParams,
  transform: (data) => {
    data.columns.forEach((column) => {
      handleFetchFromField(column);
      // handleColumnConfig(column);
    });
    if (options.value.doctype === "HD Ticket") {
      data.data.forEach((row) => {
        if (
          defaultParams.show_customer_portal_fields &&
          row.status === "Replied"
        ) {
          row.status = "Awaiting Response";
        }
      });
    }
    return data;
  },
  onSuccess: (data) => {
    list.params = defaultParams;
    columns.value = data.columns;
  },
});

const filterableFields = createResource({
  url: "helpdesk.api.doc.get_filterable_fields",
  cache: ["DocField", options.value.doctype],
  auto: !options.value.hideViewControls,
  params: {
    doctype: options.value.doctype,
    append_assign: true,
    show_customer_portal_fields: defaultParams.show_customer_portal_fields,
  },
  transform: (data) => {
    data = data.map((field) => {
      return {
        label: field.label,
        value: field.fieldname,
        ...field,
      };
    });
    return data;
  },
});
const isViewUpdated = ref(false);

function applyFilters(filters) {
  defaultParams.filters = { ...filters };
  list.submit({ ...defaultParams });
  console.log("applyFilters", filters);
}

function applySort(order_by: string) {
  defaultParams.order_by = order_by;
  list.submit({ ...defaultParams, order_by });
}

function updateColumns(obj) {
  isViewUpdated.value = true;
  const { columns: _columns, isDefault, rows } = obj;
  _columns?.forEach((column) => {
    handleFetchFromField(column);
    // handleColumnConfig(column);
  });
  columns.value = defaultParams.columns = isDefault ? "" : _columns;
  defaultParams.rows = isDefault ? "" : rows;
  list.reload({ ...defaultParams });
}

function reload(reset: boolean = false) {
  if (reset) {
    defaultParams.filters = props.default_filters || {};
    defaultParams.order_by = "modified desc";
    defaultParams.page_length = options.value.default_page_length;
    defaultParams.page_length_count = options.value.default_page_length;
    defaultParams.columns = [];
    defaultParams.rows = [];
    defaultParams.is_default = true;
  }
  list.reload({ ...defaultParams });
}

const listViewActions = {
  applyFilters,
  applySort,
  updateColumns,
  reload,
};

const filters = computed(() => {
  if (!list) return new Set();
  let allFilters = list?.params?.filters || list.data?.params?.filters;
  if (!allFilters || !filterableFields.data) return new Set();

  return convertFilters(filterableFields.data, allFilters);
});

function convertFilters(data, allFilters) {
  let f = [];
  for (let [key, value] of Object.entries(allFilters)) {
    let field = data.find((f) => f.fieldname === key);
    if (typeof value !== "object" || !value) {
      value = ["=", value];
      if (field?.fieldtype === "Check") {
        value = ["equals", value[1] ? "Yes" : "No"];
      }
    }

    if (field) {
      f.push({
        field,
        fieldname: key,
        operator: oppositeOperatorMap[value[0]],
        value: value[1],
      });
    }
  }
  return new Set(f);
}

function getOperators(fieldtype, fieldname) {
  let options = [];
  if (typeString.includes(fieldtype)) {
    options.push(
      ...[
        { label: "Equals", value: "equals" },
        { label: "Not Equals", value: "not equals" },
        { label: "Like", value: "like" },
        { label: "Not Like", value: "not like" },
        { label: "In", value: "in" },
        { label: "Not In", value: "not in" },
        { label: "Is", value: "is" },
      ]
    );
  }
  if (fieldname === "_assign") {
    // TODO: make equals and not equals work
    options = [
      { label: "Like", value: "like" },
      { label: "Not Like", value: "not like" },
      { label: "Is", value: "is" },
    ];
  }
  if (typeNumber.includes(fieldtype)) {
    options.push(
      ...[
        { label: "Equals", value: "equals" },
        { label: "Not Equals", value: "not equals" },
        { label: "Like", value: "like" },
        { label: "Not Like", value: "not like" },
        { label: "In", value: "in" },
        { label: "Not In", value: "not in" },
        { label: "Is", value: "is" },
        { label: "<", value: "<" },
        { label: ">", value: ">" },
        { label: "<=", value: "<=" },
        { label: ">=", value: ">=" },
      ]
    );
  }
  if (typeSelect.includes(fieldtype)) {
    options.push(
      ...[
        { label: "Equals", value: "equals" },
        { label: "Not Equals", value: "not equals" },
        { label: "In", value: "in" },
        { label: "Not In", value: "not in" },
        { label: "Is", value: "is" },
      ]
    );
  }
  if (typeLink.includes(fieldtype)) {
    options.push(
      ...[
        { label: "Equals", value: "equals" },
        { label: "Not Equals", value: "not equals" },
        { label: "Like", value: "like" },
        { label: "Not Like", value: "not like" },
        { label: "In", value: "in" },
        { label: "Not In", value: "not in" },
        { label: "Is", value: "is" },
      ]
    );
  }
  if (typeCheck.includes(fieldtype)) {
    options.push(...[{ label: "Equals", value: "equals" }]);
  }
  if (["Duration"].includes(fieldtype)) {
    options.push(
      ...[
        { label: "Like", value: "like" },
        { label: "Not Like", value: "not like" },
        { label: "In", value: "in" },
        { label: "Not In", value: "not in" },
        { label: "Is", value: "is" },
      ]
    );
  }
  if (typeDate.includes(fieldtype)) {
    options.push(
      ...[
        { label: "Equals", value: "equals" },
        { label: "Not Equals", value: "not equals" },
        { label: "Is", value: "is" },
        { label: ">", value: ">" },
        { label: "<", value: "<" },
        { label: ">=", value: ">=" },
        { label: "<=", value: "<=" },
        { label: "Between", value: "between" },
        { label: "Timespan", value: "timespan" },
      ]
    );
  }
  if (typeRating.includes(fieldtype)) {
    options.push(
      ...[
        { label: "Equals", value: "equals" },
        { label: "Not Equals", value: "not equals" },
        { label: "Is", value: "is" },
        { label: ">", value: ">" },
        { label: "<", value: "<" },
        { label: ">=", value: ">=" },
        { label: "<=", value: "<=" },
      ]
    );
  }
  return options;
}

function getValueControl(f) {
  const { field, operator } = f;
  const { fieldtype, options } = field;
  if (operator == "is") {
    return h(FormControl, {
      type: "select",
      options: [
        {
          label: "Set",
          value: "set",
        },
        {
          label: "Not Set",
          value: "not set",
        },
      ],
    });
  } else if (operator == "timespan") {
    return h(FormControl, {
      type: "select",
      options: timespanOptions,
    });
  } else if (["like", "not like", "in", "not in"].includes(operator)) {
    return h(FormControl, { type: "text" });
  } else if (typeSelect.includes(fieldtype) || typeCheck.includes(fieldtype)) {
    const _options =
      fieldtype == "Check" ? ["Yes", "No"] : getSelectOptions(options);
    return h(FormControl, {
      type: "select",
      options: _options.map((o) => ({
        label: o,
        value: o,
      })),
    });
  } else if (typeLink.includes(fieldtype)) {
    if (fieldtype == "Dynamic Link") {
      return h(FormControl, { type: "text" });
    }
    return h(Link, { class: "form-control", doctype: options, value: f.value });
  } else if (typeNumber.includes(fieldtype)) {
    return h(FormControl, { type: "number" });
  } else if (typeDate.includes(fieldtype) && operator == "between") {
    return h(DateRangePicker, { value: f.value, iconLeft: "" });
  } else if (typeDate.includes(fieldtype)) {
    return h(fieldtype == "Date" ? DatePicker : DateTimePicker, {
      value: f.value,
      iconLeft: "",
    });
  } else if (typeRating.includes(fieldtype)) {
    return h(StarRating, {
      rating: f.value || 0,
      static: false,
      class: "truncate",
      "onUpdate:modelValue": (v) => updateValue(v, f),
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
  if (typeDate.includes(field.fieldtype)) {
    return null;
  }
  if (typeRating.includes(field.fieldtype)) {
    return 0;
  }
  return "";
}

function getDefaultOperator(fieldtype, fieldname = null) {
  if (fieldname === "_assign") {
    return "like";
  }
  if (typeSelect.includes(fieldtype)) {
    return "equals";
  }
  if (typeCheck.includes(fieldtype) || typeNumber.includes(fieldtype)) {
    return "equals";
  }
  if (typeDate.includes(fieldtype)) {
    return "between";
  }
  if (typeLink.includes(fieldtype)) {
    return "equals";
  }
  if (typeRating.includes(fieldtype)) {
    return "equals";
  }
  return "like";
}

function getSelectOptions(options) {
  return options.split("\n");
}

function setFilter(data) {
  if (!data) return;
  filters.value.add({
    field: {
      label: data.label,
      fieldname: data.value,
      fieldtype: data.fieldtype,
      options: data.options,
    },
    fieldname: data.value,
    operator: getDefaultOperator(data.fieldtype, data.fieldname),
    value: getDefaultValue(data),
  });
  apply();
}

function updateFilter(data, index) {
  filters.value.delete(Array.from(filters.value)[index]);
  filters.value.add({
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
  apply();
}

function removeFilter(index) {
  filters.value.delete(Array.from(filters.value)[index]);
  apply();
}

function clearfilter(close) {
  filters.value.clear();
  apply();
  close && close();
}

function updateValue(value, filter) {
  value = value.target ? value.target.value : value;
  if (filter.operator === "between") {
    filter.value = [value.split(",")[0], value.split(",")[1]];
  } else {
    filter.value = value;
  }
  apply();
}

function updateOperator(event, filter) {
  let oldOperatorValue = event.target._value;
  let newOperatorValue = event.target.value;
  filter.operator = event.target.value;
  if (!isSameTypeOperator(oldOperatorValue, newOperatorValue)) {
    filter.value = getDefaultValue(filter.field);
  }
  if (newOperatorValue === "is" || newOperatorValue === "is not") {
    filter.value = "set";
  }
  apply();
}

function isSameTypeOperator(oldOperator, newOperator) {
  let textOperators = [
    "equals",
    "not equals",
    "in",
    "not in",
    ">",
    "<",
    ">=",
    "<=",
  ];
  if (
    textOperators.includes(oldOperator) &&
    textOperators.includes(newOperator)
  )
    return true;
  return false;
}

function apply() {
  let _filters = [];
  filters.value.forEach((f) => {
    _filters.push({
      fieldname: f.fieldname,
      operator: f.operator,
      value: f.value,
    });
  });
  listViewActions.applyFilters(parseFilters(_filters));
}

function parseFilters(filters) {
  const filtersArray = Array.from(filters);
  const obj = filtersArray.map(transformIn).reduce((p, c) => {
    if (["equals", "="].includes(c.operator)) {
      p[c.fieldname] =
        c.value == "Yes" ? true : c.value == "No" ? false : c.value;
    } else {
      p[c.fieldname] = [operatorMap[c.operator.toLowerCase()], c.value];
    }
    return p;
  }, {});
  const merged = { ...obj };
  return merged;
}

function transformIn(f) {
  if (f.operator.includes("like") && !f.value.includes("%")) {
    f.value = `${f.value}`;
  }
  return f;
}

const operatorMap = {
  is: "is",
  "is not": "is not",
  in: "in",
  "not in": "not in",
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
  between: "between",
  timespan: "timespan",
};

const oppositeOperatorMap = {
  is: "is",
  "=": "equals",
  "!=": "not equals",
  equals: "equals",
  "is not": "is not",
  true: "yes",
  false: "no",
  LIKE: "like",
  "NOT LIKE": "not like",
  in: "in",
  "not in": "not in",
  ">": ">",
  "<": "<",
  ">=": ">=",
  "<=": "<=",
  between: "between",
  timespan: "timespan",
};

const timespanOptions = [
  {
    label: "Last Week",
    value: "last week",
  },
  {
    label: "Last Month",
    value: "last month",
  },
  {
    label: "Last Quarter",
    value: "last quarter",
  },
  {
    label: "Last 6 Months",
    value: "last 6 months",
  },
  {
    label: "Last Year",
    value: "last year",
  },
  {
    label: "Yesterday",
    value: "yesterday",
  },
  {
    label: "Today",
    value: "today",
  },
  {
    label: "Tomorrow",
    value: "tomorrow",
  },
  {
    label: "This Week",
    value: "this week",
  },
  {
    label: "This Month",
    value: "this month",
  },
  {
    label: "This Quarter",
    value: "this quarter",
  },
  {
    label: "This Year",
    value: "this year",
  },
  {
    label: "Next Week",
    value: "next week",
  },
  {
    label: "Next Month",
    value: "next month",
  },
  {
    label: "Next Quarter",
    value: "next quarter",
  },
  {
    label: "Next 6 Months",
    value: "next 6 months",
  },
  {
    label: "Next Year",
    value: "next year",
  },
];
</script>
