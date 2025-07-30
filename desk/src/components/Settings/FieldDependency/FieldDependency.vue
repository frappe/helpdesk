<template>
  <div class="h-full flex flex-col">
    <header
      class="flex justify-between mb-8 sticky top-0 z-10 bg-surface-modal items-center"
    >
      <div class="flex items-center gap-2">
        <Button
          variant="ghost"
          icon-left="chevron-left"
          :label="dependencyLabel"
          size="md"
          @click="handleBackNavigation"
          class="cursor-pointer hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 pl-0 -ml-[5px] pr-0"
        />
        <Badge v-if="isDirty" theme="orange"> Unsaved Changes </Badge>
      </div>

      <div class="flex gap-4">
        <!-- Switch -->
        <div class="flex gap-2 items-center">
          <Switch v-model="state.enabled" class="!w-fit" />
          <span class="text-p-base text-ink-gray-6">Enabled</span>
        </div>
        <!-- Actions -->
        <div class="flex gap-1">
          <Button
            label="Save"
            variant="solid"
            size="sm"
            :disabled="
              !state.selectedParentField ||
              !state.selectedChildField ||
              Object.keys(state.childSelections).length === 0
            "
            @click="handleSubmit"
          />
        </div>
      </div>
    </header>
    <!-- Form -->
    <form
      @submit.prevent="handleSubmit"
      class="w-full flex-1 flex flex-col gap-8 h-full"
    >
      <!-- Field Selection -->
      <div class="flex gap-3 w-full justify-between">
        <FormControl
          v-model="state.selectedParentField"
          label="Parent Field"
          placeholder="Select Parent Field"
          required
          class="flex-1"
          type="select"
          :options="parentFields"
          :disabled="!isNew"
        />
        <FormControl
          v-model="state.selectedChildField"
          label="Child Field"
          placeholder="Select Child Field"
          required
          class="flex-1"
          :disabled="!state.selectedParentField || !isNew"
          type="select"
          :options="state.childFields"
        />
      </div>
      <!-- Value Selection -->
      <div class="flex w-full flex-1 justify-between h-full">
        <!-- left box -->
        <div class="flex-1 flex flex-col gap-1.5">
          <span class="block text-xs text-ink-gray-5">
            Select parent field value
          </span>
          <div
            class="border flex-1 border-r-0 rounded-l p-2 flex flex-col gap-2"
          >
            <template v-if="state.selectedParentField">
              <FormControl
                v-model="state.parentSearch"
                :placeholder="parentPlaceholder"
                type="text"
                class="w-full"
              >
                <template #prefix>
                  <LucideSearch class="h-4 w-4 text-gray-500" />
                </template>
              </FormControl>
              <div class="flex-1 overflow-y-auto hide-scrollbar basis-0">
                <ul>
                  <li
                    v-for="value in filteredParentFieldValues"
                    :key="value"
                    class="py-2 mb-1 px-2.5 cursor-pointer rounded flex justify-between items-center hover:bg-surface-gray-1"
                    :class="{
                      'bg-surface-gray-2 hover:bg-surface-gray-3':
                        state.currentParentSelection === value,
                    }"
                    @click="handleParentValueClick(value)"
                  >
                    <span class="text-base text-ink-gray-6">{{ value }}</span>
                    <LucideChevronRight
                      class="h-4 w-4 text-ink-gray-6"
                      v-if="
                        getSelectedChildValueCount(value) === 0 ||
                        state.currentParentSelection === value
                      "
                    />
                    <Badge
                      v-else
                      :label="getSelectedChildValueCount(value)"
                      :theme="'gray'"
                      variant="subtle"
                      class="!h-4"
                    />
                  </li>
                </ul>
              </div>
            </template>
            <template v-else>
              <div
                class="flex flex-col items-center mt-20 h-full text-ink-gray-4 text-sm"
              >
                Please select a parent field first
              </div>
            </template>
          </div>
        </div>
        <!-- right box -->
        <div class="flex-1 flex flex-col gap-1.5">
          <span class="block text-xs text-ink-gray-5 pl-1.5">
            Select child field value
          </span>
          <div class="border flex-1 rounded-r p-2 flex flex-col gap-2">
            <template
              v-if="state.selectedChildField && state.currentParentSelection"
            >
              <FormControl
                v-model="state.childSearch"
                :placeholder="childPlaceholder"
                type="text"
                class="w-full"
              >
                <template #prefix>
                  <LucideSearch class="h-4 w-4 text-gray-500" />
                </template>
              </FormControl>
              <div class="flex-1 overflow-y-auto hide-scrollbar basis-0">
                <!-- Master Check box -->
                <li
                  class="py-2 mb-1 px-2.5 cursor-pointer rounded flex items-center bg-surface-gray-1 hover:bg-surface-gray-2"
                  @click="handleSelectAllChildValues(!toggleAllChildValues)"
                >
                  <FormControl
                    type="checkbox"
                    :model-value="toggleAllChildValues"
                    class="mr-2"
                  />
                  <span class="text-base text-ink-gray-8 font-medium">
                    {{ toggleCheckboxLabel }}
                  </span>
                </li>
                <ul>
                  <li
                    v-for="value in filteredChildFieldValues"
                    :key="value"
                    class="py-2 mb-1 px-2.5 cursor-pointer rounded flex items-center hover:bg-surface-gray-1 max-w-full truncate"
                    @click="handleChildValueClick(value)"
                  >
                    <FormControl
                      type="checkbox"
                      :model-value="isChildValueSelected(value)"
                      class="mr-2"
                    />
                    <span class="text-base text-ink-gray-6">{{ value }}</span>
                  </li>
                </ul>
              </div>
            </template>
            <template v-else-if="!state.selectedChildField">
              <div
                class="flex flex-col items-center mt-20 h-full text-ink-gray-4 text-sm"
              >
                Please select a child field first
              </div>
            </template>
            <template v-else>
              <div
                class="flex flex-col items-center mt-20 h-full text-ink-gray-4 text-sm"
              >
                Please select a parent value first
              </div>
            </template>
          </div>
        </div>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { getMeta } from "@/stores/meta";
import { getFieldDependencyLabel } from "@/utils";
import { createResource, FormControl, toast, Switch, Badge } from "frappe-ui";
import { reactive, watch, computed } from "vue";
import { getFieldOptions, hiddenChildFields } from "./fieldDependency";
import { globalStore } from "@/stores/globalStore";

const props = defineProps({
  fieldDependencyName: {
    type: String,
    default: "",
  },
});
const emit = defineEmits(["update:step"]);

const { $dialog } = globalStore();

const isNew = computed(() => !props.fieldDependencyName);

const dependencyLabel = computed(() => {
  if (isNew.value) return "New Field Dependency";
  return getFieldDependencyLabel(props.fieldDependencyName);
});

const parentPlaceholder = computed(() => {
  if (!state.selectedParentField) return "Search values";
  let label = parentFields.value.find(
    (f) => f.value === state.selectedParentField
  )?.label;
  return `Search ${label} values`;
});
const childPlaceholder = computed(() => {
  if (!state.currentParentSelection) return "Search values";
  return `Search ${state.currentParentSelection} values`;
});

const { getFields } = getMeta("HD Ticket");

const parentFields = computed(() => {
  let _fields = getFields();

  if (!_fields || _fields.length === 0) {
    return [];
  }
  _fields = _fields.filter(
    (f) => f.fieldtype === "Select" || f.fieldtype === "Link"
  );
  return _fields.map((f) => ({
    label: f.label,
    value: f.fieldname,
    options: f.options || [],
    type: f.fieldtype,
  }));
});

const state = reactive({
  selectedParentField: "",
  selectedChildField: "",
  childFields: [],

  parentFieldValues: [],
  childFieldValues: [],

  currentParentSelection: "",

  childSelections: {}, // Initial value is a Set
  initialChildSelections: {},
  parentSearch: "",
  childSearch: "",

  enabled: true,
});

const isDirty = computed(() => {
  if (isNew.value) {
    return state.enabled !== true || state.selectedParentField !== "";
  }
  if (fieldDependency.loading) return false;
  return (
    Boolean(fieldDependency.data?.enabled) !== Boolean(state.enabled) ||
    stringifyParentChildMapping(state.childSelections) !==
      stringifyParentChildMapping(state.initialChildSelections)
  );
});

const filteredParentFieldValues = computed(() => {
  if (!state.parentSearch) return state.parentFieldValues;
  return state.parentFieldValues.filter((v) =>
    v.toLowerCase().includes(state.parentSearch.toLowerCase())
  );
});

const filteredChildFieldValues = computed(() => {
  if (!state.childSearch) return state.childFieldValues;
  return state.childFieldValues.filter((v) =>
    v.toLowerCase().includes(state.childSearch.toLowerCase())
  );
});

function getSelectedChildValueCount(parent) {
  const selectedCount =
    state.childSelections[parent] instanceof Set
      ? state.childSelections[parent].size
      : 0;
  return selectedCount;
}

const createUpdateFieldDependency = createResource({
  url: "helpdesk.api.settings.field_dependency.create_update_field_dependency",
  auto: false,
  makeParams: () => ({
    parent_field: state.selectedParentField,
    child_field: state.selectedChildField,
    parent_child_mapping: stringifyParentChildMapping(),
    enabled: state.enabled,
  }),
  onSuccess: () => {
    if (!isNew.value) {
      fieldDependency.reload();
      return;
    }
    emit("update:step", "fd-list");
  },
});

const fieldDependency = createResource({
  url: "helpdesk.api.settings.field_dependency.get_field_dependency",
  params: {
    name: props.fieldDependencyName,
  },
  auto: !isNew.value,
  onSuccess: (data) => {
    state.selectedParentField = data.parent_field;
    state.selectedChildField = data.child_field;
    state.enabled = data.enabled;

    const mapping = JSON.parse(data.parent_child_mapping || "{}");
    let selections = {};
    Object.keys(mapping).forEach((parent) => {
      selections[parent] = new Set(mapping[parent]);
    });
    state.childSelections = selections;
    // for checking dirty state
    state.initialChildSelections = structuredClone(selections);

    if (!state.currentParentSelection) {
      state.currentParentSelection = Object.keys(mapping)[0] || "";
    }
  },
});

function stringifyParentChildMapping(selections = null) {
  const _selections =
    selections && Object.keys(selections).length > 0
      ? selections
      : state.childSelections;
  const mapping = {};
  Object.keys(_selections).forEach((parent) => {
    let selections = Array.from(_selections[parent]);
    if (selections.length) {
      mapping[parent] = Array.from(_selections[parent]);
    }
  });
  return JSON.stringify(mapping);
}

async function handleFieldValues(fieldname: string, isParentField: boolean) {
  if (!fieldname) return [];

  if (isParentField) {
    // if new field dependency, reset child fields
    if (isNew.value) {
      state.selectedChildField = ""; // Reset child field when parent changes
      state.childFieldValues = [];
      state.currentParentSelection = ""; // Reset current parent selection
      state.childSelections = {}; // Reset child selections for new parent

      // filter out hidden already madeup field dependencies in the child fields
      let fieldsToHide = [fieldname, ...hiddenChildFields.value];
      state.childFields = parentFields.value.filter(
        (f) => !fieldsToHide.includes(f.value)
      );
    } else {
      state.childFields = parentFields.value.filter(
        (f) => f.value === state.selectedChildField
      );
    }
    // show the selected child field if editing
  }

  const field = isParentField
    ? parentFields.value.find((f) => f.value === fieldname)
    : state.childFields.find((f) => f.value === fieldname);
  if (!field) return [];
  let options = await getFieldOptions(field);

  return options;
}

function handleParentValueClick(value) {
  state.currentParentSelection = value;
}

function handleChildValueClick(childValue) {
  const parent = state.currentParentSelection;
  if (!parent) return;
  if (!(state.childSelections[parent] instanceof Set)) {
    state.childSelections[parent] = new Set();
  }
  if (state.childSelections[parent].has(childValue)) {
    state.childSelections[parent].delete(childValue);
  } else {
    state.childSelections[parent].add(childValue);
  }
}

function isChildValueSelected(childValue) {
  const parent = state.currentParentSelection;
  return (
    state.childSelections[parent] instanceof Set &&
    state.childSelections[parent].has(childValue)
  );
}

const toggleAllChildValues = computed({
  get() {
    const parent = state.currentParentSelection;
    if (!parent) return false;
    // If no child values are selected, return false
    if (!(state.childSelections[parent] instanceof Set)) {
      return false;
    }
    // If all filtered child values are selected, return true
    return (
      state.childSelections[parent].size ===
      filteredChildFieldValues.value.length
    );
  },
  set(value) {
    handleSelectAllChildValues(value);
  },
});

const toggleCheckboxLabel = computed(() => {
  const parent = state.currentParentSelection;
  if (!parent) return "Select All";
  const selectedCount = getSelectedChildValueCount(parent);
  if (selectedCount === 0) return "Select All";
  return `${selectedCount} ${
    selectedCount === 1 ? "value" : "values"
  } selected`;
});

function handleSelectAllChildValues(value) {
  const parent = state.currentParentSelection;
  if (!parent) return;

  if (!(state.childSelections[parent] instanceof Set)) {
    state.childSelections[parent] = new Set();
  }

  if (value) {
    // Select all child values
    filteredChildFieldValues.value.forEach((childValue) => {
      state.childSelections[parent].add(childValue);
    });
  } else {
    // Deselect all child values
    state.childSelections[parent].clear();
  }
}

function handleBackNavigation() {
  if (isDirty.value) {
    $dialog({
      title: "Unsaved Changes",
      message:
        "Are you sure you want to go back? Unsaved changes will be lost.",
      actions: [
        {
          label: "Confirm",
          variant: "solid",
          onClick({ close }) {
            close();
            emit("update:step", "fd-list");
          },
        },
      ],
    });
    return;
  }
  emit("update:step", "fd-list");
}

function handleSubmit() {
  if (!isDirty.value) return;
  createUpdateFieldDependency.submit();
  let successMessage = isNew.value
    ? "Field Dependency created successfully"
    : "Field Dependency updated successfully";
  toast.success(successMessage);
}

// parent field watcher
watch(
  () => state.selectedParentField,
  async (newParentField) => {
    state.parentFieldValues = await handleFieldValues(newParentField, true);
  }
);

// child field watcher
watch(
  () => state.selectedChildField,
  async (newChildField) => {
    state.childFieldValues = await handleFieldValues(newChildField, false);
  }
);

watch(
  () => state.currentParentSelection,
  () => {
    state.childSearch = ""; // Reset child search when parent selection changes
  }
);
</script>
