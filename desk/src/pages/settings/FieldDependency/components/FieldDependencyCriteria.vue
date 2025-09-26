<template>
  <div class="flex justify-between items-start flex-col gap-6">
    <span class="text-sm text-ink-gray-5 pt-4 w-full"
      >Set visibility and mandatory criteria for
      {{ selections.childField || "child" }} field:</span
    >
    <div class="flex flex-col gap-4 w-full pb-2">
      <!-- Display Criteria -->
      <div class="flex items-center gap-3 justify-between">
        <div class="flex gap-3 items-center">
          <Switch v-model="fieldCriteriaState.display.enabled" />
          <div class="flex items-center gap-1">
            <span class="text-sm text-ink-gray-5"
              >Show {{ selections.childField }} if
              {{ selections.parentField }} is set to</span
            >
            <DocumentationButton
              url="https://docs.frappe.io/helpdesk/field-dependency#handling-visibility-of-child-field"
              color="!text-ink-gray-6"
            />
          </div>
        </div>
        <MultiSelectCombobox
          :disabled="!fieldCriteriaState.display.enabled"
          class="min-w-[120px] max-w-[120px]"
          :options="fieldCriteriaOptions"
          :model-value="fieldCriteriaState.display.value"
          @update:model-value="handleCriteriaSelection($event, 'display')"
          :multiple="true"
          placeholder="Select Child Field values"
          placement="top"
        />
      </div>
      <!-- Mandatory Criteria -->
      <div class="flex items-center gap-3 justify-between w-full">
        <div class="flex gap-3 items-center">
          <Switch v-model="fieldCriteriaState.mandatory.enabled" />
          <div class="flex items-center gap-1">
            <span class="text-sm text-ink-gray-5"
              >Make {{ selections.childField }} mandatory if
              {{ selections.parentField }} is set to</span
            >
            <DocumentationButton
              url="https://docs.frappe.io/helpdesk/field-dependency#handling-if-the-child-field-is-mandatory"
              color="!text-ink-gray-6"
            />
          </div>
        </div>
        <MultiSelectCombobox
          :disabled="!fieldCriteriaState.mandatory.enabled"
          class="min-w-[120px] max-w-[120px]"
          :options="fieldCriteriaOptions"
          :model-value="fieldCriteriaState.mandatory.value"
          @update:model-value="handleCriteriaSelection($event, 'mandatory')"
          :multiple="true"
          placeholder="Select Child Field values"
          placement="top"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import DocumentationButton from "@/components/DocumentationButton.vue";
import MultiSelectCombobox from "@/components/frappe-ui/MultiSelectCombobox.vue";
import { getMeta } from "@/stores/meta";
import { Switch } from "frappe-ui";
import { computed } from "vue";

const props = defineProps<{
  parentFieldValues: string[];
}>();

const fieldCriteriaState = defineModel<{
  display: { enabled: boolean; value: Record<"label" | "value", string>[] };
  mandatory: { enabled: boolean; value: Record<"label" | "value", string>[] };
}>();
const state = defineModel("selections") as any;

const { getField } = getMeta("HD Ticket");

const selections = computed(() => {
  let childField = state.value.selectedChildField;
  let parentField = state.value.selectedParentField;
  childField = getField(childField)?.label;
  parentField = getField(parentField)?.label;
  return { childField, parentField };
});

const fieldCriteriaOptions = computed(() => {
  const _options = [{ label: "Any", value: "Any" }];
  props.parentFieldValues.forEach((value) => {
    if (!_options.some((o) => o.value === value)) {
      _options.push({ label: value, value });
    }
  });
  return _options;
});

function handleCriteriaSelection(
  values: { label: string; value: string }[],
  stateKey: "display" | "mandatory"
) {
  const _values = values.map((v) => v.value);
  fieldCriteriaState.value[stateKey].value = values;
  if (_values.length === 0) {
    fieldCriteriaState.value[stateKey].value = [{ label: "Any", value: "Any" }];
  } else if (_values[0] === "Any" && _values.length > 1) {
    fieldCriteriaState.value[stateKey].value = _values
      .filter((value) => value !== "Any")
      .map((value) => ({ label: value, value }));
  } else if (_values.at(-1) === "Any" && _values.length > 1) {
    fieldCriteriaState.value[stateKey].value = [{ label: "Any", value: "Any" }];
  }
}
</script>

<style scoped></style>
