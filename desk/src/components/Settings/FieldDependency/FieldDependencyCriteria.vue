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
        <MultiSelect
          class="min-w-[120px] max-w-[120px]"
          side="top"
          :disabled="!fieldCriteriaState.display.enabled"
          :options="fieldCriteriaOptions"
          :model-value="selectedValues('display')"
          :placeholder="__('Select Child Field values')"
          @update:model-value="handleCriteriaSelection($event, 'display')"
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
        <MultiSelect
          class="min-w-[120px] max-w-[120px]"
          side="top"
          :disabled="!fieldCriteriaState.mandatory.enabled"
          :options="fieldCriteriaOptions"
          :model-value="selectedValues('mandatory')"
          :placeholder="__('Select Child Field values')"
          @update:model-value="handleCriteriaSelection($event, 'mandatory')"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import DocumentationButton from "@/components/DocumentationButton.vue";
import { getMeta } from "@/stores/meta";
import { __ } from "@/translation";
import { MultiSelect, Switch } from "frappe-ui";
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

function selectedValues(stateKey: "display" | "mandatory") {
  return fieldCriteriaState.value[stateKey].value.map((v) => v.value);
}

function handleCriteriaSelection(
  values: string[],
  stateKey: "display" | "mandatory"
) {
  // "Any" is exclusive: picking it drops the rest, picking anything else drops it
  const wasAnySelected = selectedValues(stateKey).includes("Any");
  let selected =
    values.includes("Any") && !wasAnySelected
      ? ["Any"]
      : values.filter((value) => value !== "Any");
  if (!selected.length) selected = ["Any"];
  fieldCriteriaState.value[stateKey].value = selected.map((value) => ({
    label: value,
    value,
  }));
}
</script>

<style scoped></style>
