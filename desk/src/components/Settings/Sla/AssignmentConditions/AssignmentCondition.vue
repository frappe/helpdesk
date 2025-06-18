<template>
  <div
    :class="[
      'flex gap-2',
      {
        'items-center': props.condition.field != 'group',
      },
    ]"
  >
    <div
      :class="[
        'flex gap-2 w-full',
        {
          'items-center justify-between': props.condition.field != 'group',
        },
      ]"
    >
      <div
        :class="[
          'min-w-12 text-end text-base text-gray-600',
          {
            // 'mt-2': props.condition.field == 'group' && !props.isChild,
            // hidden: props.condition.field == 'group' && props.isChild,
          },
        ]"
      >
        <span v-if="props.itemIndex == 0"> Where </span>
        <span v-else>
          <Dropdown
            class="w-full"
            :options="[
              {
                label: 'And',
                onClick: () => {
                  props.condition.conjunction = 'and';
                },
              },
              {
                label: 'Or',
                onClick: () => {
                  props.condition.conjunction = 'or';
                },
              },
            ]"
            :button="{
              label: props.condition.conjunction,
            }"
          >
            <template #default>
              <Button variant="subtle" class="w-full">
                {{ props.condition.conjunction }}
              </Button>
            </template>
          </Dropdown>
        </span>
      </div>
      <div
        v-if="props.condition.field != 'group'"
        class="flex items-center gap-2 w-full"
      >
        <div id="fieldname" class="w-full">
          <AutocompleteNew
            :options="filterableFields.data"
            v-model="props.condition.field"
            :placeholder="'First Name'"
          />
        </div>
        <div id="operator">
          <FormControl
            :disabled="!props.condition.field"
            type="select"
            v-model="props.condition.operator"
            @change="updateOperator"
            :options="getOperators()"
            :placeholder="'Equals'"
            class="w-max min-w-[50px]"
          />
        </div>
        <div id="value" class="w-full">
          <FormControl
            v-if="!props.condition.field"
            disabled
            type="text"
            :placeholder="'condition'"
            class="w-full"
          />
          <component
            v-else
            :is="getValueControl()"
            v-model="props.condition.value"
            @change="updateValue"
            :placeholder="'condition'"
          />
        </div>
      </div>
      <AssignmentConditions
        v-if="
          props.condition.field == 'group' &&
          !(props.level == 2 || props.level == 4)
        "
        :conditions="props.condition.value"
        :isChild="true"
        :level="props.level"
      />
      <Button
        variant="outline"
        v-if="
          props.condition.field == 'group' &&
          (props.level == 2 || props.level == 4)
        "
        @click="show = true"
      >
        Open nested conditions
      </Button>
    </div>
    <div :class="'w-max'">
      <Dropdown
        :options="[
          props.condition.field != 'group' &&
            props.level < 4 && {
              label: 'Turn into a group',
              icon: () => h(GroupIcon),
              onClick: () => {
                turnIntoGroup();
              },
            },
          {
            label: 'Remove',
            icon: 'trash-2',
            onClick: () => {
              emit('remove');
            },
          },
        ]"
      >
        <Button variant="ghost">
          <template #icon>
            <FeatherIcon name="more-horizontal" class="h-4 w-4" />
          </template>
        </Button>
      </Dropdown>
    </div>
  </div>
  <Dialog v-model="show" :options="{ size: '2xl', title: 'Nested conditions' }">
    <!-- <template #body-title>
      <span class="text-lg">Nested conditions</span>
    </template> -->
    <template #body-content>
      <AssignmentConditions
        :conditions="props.condition.value"
        :isChild="true"
        :level="props.level"
      />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
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
import GroupIcon from "~icons/lucide/group";
import { h, defineEmits, ref, onMounted } from "vue";
import AssignmentConditions from "./AssignmentConditions.vue";
import { Dialog } from "frappe-ui";

const show = ref(false);
const emit = defineEmits(["remove"]);
const props = defineProps({
  condition: {
    type: Object,
    required: true,
  },
  doctype: {
    type: String,
    required: true,
  },
  isChild: {
    type: Boolean,
    default: false,
  },
  itemIndex: {
    type: Number,
  },
  level: {
    type: Number,
    default: 0,
  },
});

const typeCheck = ["Check"];
const typeLink = ["Link", "Dynamic Link"];
const typeNumber = ["Float", "Int", "Currency", "Percent"];
const typeSelect = ["Select"];
const typeString = ["Data", "Long Text", "Small Text", "Text Editor", "Text"];
const typeDate = ["Date", "Datetime"];
const typeRating = ["Rating"];

const filterableFields = createResource({
  url: "helpdesk.api.doc.get_filterable_fields",
  cache: ["DocField", props.doctype],
  auto: true,
  params: {
    doctype: props.doctype,
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

function getValueControl() {
  const { field, operator } = props.condition;
  if (!field) return null;
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
    return h(Link, {
      class: "form-control",
      doctype: options,
      value: props.condition.value,
    });
  } else if (typeNumber.includes(fieldtype)) {
    return h(FormControl, { type: "number" });
  } else if (typeDate.includes(fieldtype) && operator == "between") {
    return h(DateRangePicker, { value: props.condition.value, iconLeft: "" });
  } else if (typeDate.includes(fieldtype)) {
    return h(fieldtype == "Date" ? DatePicker : DateTimePicker, {
      value: props.condition.value,
      iconLeft: "",
    });
  } else if (typeRating.includes(fieldtype)) {
    return h(StarRating, {
      rating: props.condition.value || 0,
      static: false,
      class: "truncate",
      "onUpdate:modelValue": (v) => updateValue(v),
    });
  } else {
    return h(FormControl, { type: "text" });
  }
}

function updateValue(value) {
  value = value.target ? value.target.value : value;
  if (props.condition.operator === "between") {
    props.condition.value = [value.split(",")[0], value.split(",")[1]];
  } else {
    props.condition.value = value;
  }
  // apply();
}

function getSelectOptions(options) {
  return options.split("\n");
}

function updateOperator(event) {
  let oldOperatorValue = event.target._value;
  let newOperatorValue = event.target.value;
  props.condition.operator = event.target.value;
  if (!isSameTypeOperator(oldOperatorValue, newOperatorValue)) {
    props.condition.value = getDefaultValue(props.condition.field);
  }
  // if (newOperatorValue === "is" || newOperatorValue === "is not") {
  //   filter.value = "set";
  // }
  // apply();
}

function getOperators() {
  let options = [];
  const { field } = props.condition;
  if (!field) return options; // Return empty options if field is null/undefined
  const { fieldtype, fieldname } = field;
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

function transformIn(f) {
  if (f.operator.includes("like") && !f.value.includes("%")) {
    f.value = `${f.value}`;
  }
  return f;
}

const turnIntoGroup = () => {
  // console.log("turning into group", props.condition.valueOf());
  const obj = Object.assign({}, props.condition);
  obj.value = props.condition;
  // props.condition.value = [props.condition.valueOf()];
  // props.condition.field = "group";
  // console.log("obj", obj, props.condition);
  props.condition.field = "group";
  props.condition.value = [obj];
  // props.condition.value = [Object.assign({}, props.condition.value)];
  console.log("turning into group", props.condition, obj);
};

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

onMounted(() => {
  filterableFields.submit();
});
</script>
