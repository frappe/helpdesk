<template>
  <div class="flex flex-col py-8 gap-8 overflow-y-hidden">
    <SettingsLayoutHeader>
      <template #title>
        <div class="flex items-center gap-2 pl-10">
          <Button
            variant="ghost"
            icon-left="chevron-left"
            :label="dependencyLabel"
            size="md"
            @click="handleBackNavigation"
            class="cursor-pointer hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 pl-0 -ml-[5px] pr-0"
          />
          <Badge v-if="isDirty" theme="orange"> Unsaved </Badge>
        </div>
      </template>
      <template #actions>
        <div class="flex gap-4 pr-10">
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
              :loading="createUpdateFieldDependency.loading"
              @click="handleSubmit"
            />
          </div>
        </div>
      </template>
    </SettingsLayoutHeader>
    <!-- Body -->
    <div class="w-full flex-1 flex flex-col gap-8 overflow-y-hidden px-10">
      <!-- Field Selection -->
      <FieldDependencyFieldsSelection
        v-model="state"
        :is-new="isNew"
        :parent-fields="parentFields"
      />

      <div class="flex flex-col gap-8 overflow-y-scroll">
        <!-- Value Selection -->
        <FieldDependencyValueSelection
          v-model="state"
          :is-new="isNew"
          :parent-fields="parentFields"
        />

        <!-- Criteria selection -->
        <FieldDependencyCriteria
          :parent-field-values="state.parentFieldValues"
          v-model="fieldCriteriaState"
          v-model:selections="state"
        />
      </div>
    </div>
  </div>
  <ConfirmDialog
    v-model="showConfirmDialog"
    title="Unsaved changes"
    message="Are you sure you want to go back? Unsaved changes will be lost."
    :onConfirm="() => $emit('update:step', 'fd-list')"
    :onCancel="() => (showConfirmDialog = false)"
  />
</template>

<script setup lang="ts">
import ConfirmDialog from "@/components/ConfirmDialog.vue";
import { getMeta } from "@/stores/meta";
import { getFieldDependencyLabel } from "@/utils";
import { createResource, Switch, toast } from "frappe-ui";
import { computed, reactive, ref, watch } from "vue";
import SettingsLayoutHeader from "../SettingsLayoutHeader.vue";
import { disableSettingModalOutsideClick } from "../settingsModal";
import { getFieldOptions, hiddenChildFields } from "./fieldDependency";
import FieldDependencyCriteria from "./FieldDependencyCriteria.vue";
import FieldDependencyFieldsSelection from "./FieldDependencyFieldsSelection.vue";
import FieldDependencyValueSelection from "./FieldDependencyValueSelection.vue";

const props = defineProps({
  fieldDependencyName: {
    type: String,
    default: "",
  },
});
const emit = defineEmits(["update:step"]);

const isNew = computed(() => !props.fieldDependencyName);

const dependencyLabel = computed(() => {
  if (isNew.value) return "New Field Dependency";
  return getFieldDependencyLabel(props.fieldDependencyName);
});

const { getFields } = getMeta("HD Ticket");

const parentFields = computed(() => {
  let _fields = getFields();

  if (!_fields || _fields.length === 0) {
    return [];
  }
  const notAllowedFields = ["status", "agreement_status"];
  _fields = _fields.filter(
    (f) =>
      (f.fieldtype === "Select" || f.fieldtype === "Link") &&
      !notAllowedFields.includes(f.fieldname)
  );
  return _fields.map((f) => ({
    label: f.label,
    value: f.fieldname,
    options: f.options || [],
    type: f.fieldtype,
  }));
});

let state = reactive({
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

let fieldCriteriaState = reactive({
  display: {
    enabled: true,
    value: [{ label: "Any", value: "Any" }],
  },
  mandatory: {
    enabled: true,
    value: [{ label: "Any", value: "Any" }],
  },
});

const createUpdateFieldDependency = createResource({
  url: "helpdesk.api.settings.field_dependency.create_update_field_dependency",
  auto: false,
  makeParams: () => ({
    parent_field: state.selectedParentField,
    child_field: state.selectedChildField,
    parent_child_mapping: stringifyParentChildMapping(),
    enabled: state.enabled,
    fields_criteria: JSON.stringify(fieldCriteriaState),
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
    parseMapping(data.parent_child_mapping);
    parseFieldCriteria(data.fields_criteria);
  },
});
function parseMapping(data: string) {
  const mapping = JSON.parse(data || "{}");
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
}

function parseFieldCriteria(data: string) {
  const criteria = JSON.parse(data || "{}");
  fieldCriteriaState.display = criteria.display || {
    enabled: true,
    value: [{ label: "Any", value: "Any" }],
  };
  fieldCriteriaState.mandatory = criteria.mandatory || {
    enabled: true,
    value: [{ label: "Any", value: "Any" }],
  };
}

const isDirty = computed(() => {
  if (isNew.value) {
    return state.enabled !== true || state.selectedParentField !== "";
  }
  if (fieldDependency.loading) return false;
  return (
    Boolean(fieldDependency.data?.enabled) !== Boolean(state.enabled) ||
    stringifyParentChildMapping(state.childSelections) !==
      stringifyParentChildMapping(state.initialChildSelections) ||
    JSON.stringify(fieldCriteriaState) !== fieldDependency.data?.fields_criteria
  );
});

watch(
  () => isDirty.value,
  (val) => {
    disableSettingModalOutsideClick.value = val;
  }
);

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

const showConfirmDialog = ref(false);
function handleBackNavigation() {
  if (createUpdateFieldDependency.loading) return;
  if (isDirty.value) {
    showConfirmDialog.value = true;

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
    // Reset child selections when child field changes
    if (isNew.value) {
      state.childSelections = {};
    }
    state.currentParentSelection = state.parentFieldValues[0] || "";
  }
);

watch(
  () => state.currentParentSelection,
  () => {
    state.childSearch = ""; // Reset child search when parent selection changes
  }
);
</script>
