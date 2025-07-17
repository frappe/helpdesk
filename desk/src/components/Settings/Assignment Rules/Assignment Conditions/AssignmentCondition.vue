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
      <div :class="'text-end text-base text-gray-600'">
        <div v-if="props.itemIndex == 0" class="min-w-16 text-start">Where</div>
        <div v-else class="min-w-16 flex items-start">
          <Button
            variant="subtle"
            class="w-max"
            @click="updateConjunction"
            :disabled="props.itemIndex > 1"
            icon-right="refresh-cw"
            :label="props.condition.conjunction"
          />
        </div>
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
            v-if="!props.condition.field"
            disabled
            type="text"
            :placeholder="'operator'"
            class="w-[100px]"
          />
          <FormControl
            v-else
            :disabled="!props.condition.field"
            type="select"
            v-model="props.condition.operator"
            @change="updateOperator"
            :options="getOperators()"
            :placeholder="'Equals'"
            class="w-max min-w-[100px]"
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
        label="Open nested conditions"
      />
    </div>
    <div :class="'w-max'">
      <Dropdown placement="right" :options="dropdownOptions">
        <Button variant="ghost" icon="more-horizontal" />
      </Dropdown>
    </div>
  </div>
  <Dialog v-model="show" :options="{ size: '3xl', title: 'Nested conditions' }">
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
  DatePicker,
  DateTimePicker,
  DateRangePicker,
  Button,
  Dialog,
  Dropdown,
} from "frappe-ui";
import { AutocompleteNew, Link, StarRating } from "@/components";
import GroupIcon from "~icons/lucide/group";
import UnGroupIcon from "~icons/lucide/ungroup";
import { h, defineEmits, ref, computed } from "vue";
import { TemplateOption } from "@/utils";
import AssignmentConditions from "./AssignmentConditions.vue";
import { filterableFields } from "@/stores/assignmentRules";

const show = ref(false);
const emit = defineEmits(["remove", "unGroupConditions", "updateConjunction"]);
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

const dropdownOptions = computed(() => {
  const options = [];

  if (props.condition.field != "group" && props.level < 4) {
    options.push({
      label: "Turn into a group",
      icon: () => h(GroupIcon),
      onClick: () => {
        turnIntoGroup();
      },
    });
  }

  if (props.condition.field == "group") {
    options.push({
      label: "Ungroup conditions",
      icon: () => h(UnGroupIcon),
      onClick: () => {
        emit("unGroupConditions");
      },
    });
  }

  options.push({
    label: "Remove",
    component: (props) =>
      TemplateOption({
        option: "Remove",
        icon: "trash-2",
        active: props.active,
        variant: "danger",
        onClick: () => {
          emit("remove");
        },
      }),
    condition: () => props.condition.field != "group",
  });

  options.push({
    label: "Remove group",
    component: (props) =>
      TemplateOption({
        option: "Remove group",
        icon: "trash-2",
        active: props.active,
        variant: "danger",
        onClick: () => {
          emit("remove");
        },
      }),
    condition: () => props.condition.field == "group",
  });

  return options;
});

const typeCheck = ["Check"];
const typeLink = ["Link", "Dynamic Link"];
const typeNumber = ["Float", "Int", "Currency", "Percent"];
const typeSelect = ["Select"];
const typeString = ["Data", "Long Text", "Small Text", "Text Editor", "Text"];
const typeDate = ["Date", "Datetime"];
const typeRating = ["Rating"];

function updateConjunction() {
  emit("updateConjunction");
}

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
}

function getOperators() {
  let options = [];
  const { field } = props.condition;
  if (!field) return options;
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

const turnIntoGroup = () => {
  const obj = Object.assign({}, props.condition);
  props.condition.field = "group";
  props.condition.value = [obj];
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
