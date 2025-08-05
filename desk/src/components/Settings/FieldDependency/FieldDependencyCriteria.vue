<template>
  <div class="flex justify-between items-start">
    <span class="text-sm text-ink-gray-5 pt-[5px]"
      >Set visibility and mandatory criteria for child field:</span
    >
    <div class="flex flex-col gap-3">
      <div class="flex items-center gap-2 justify-start">
        <Switch v-model="fieldCriteriaState.display.enabled" />
        <span class="text-sm text-ink-gray-5"
          >Show child if parent field is set to</span
        >
        <MultiSelectCombobox
          :disabled="!fieldCriteriaState.display.enabled"
          class="min-w-[120px] max-w-[120px] [&>div>button]:!h-[22px] [&>div>button]:!rounded-[6px]"
          :options="fieldCriteriaOptions"
          :model-value="fieldCriteriaState.display.value"
          @update:model-value="handleCriteriaSelection($event, 'display')"
          :multiple="true"
          placeholder="Select Child Field values"
        />
      </div>
      <div class="flex items-center gap-2 justify-start">
        <Switch v-model="fieldCriteriaState.mandatory.enabled" />
        <span class="text-sm text-ink-gray-5"
          >Make child mandatory if parent is set to</span
        >
        <MultiSelectCombobox
          :disabled="!fieldCriteriaState.mandatory.enabled"
          class="min-w-[97px] max-w-[97px] [&>div>button]:!h-[22px] [&>div>button]:!rounded-[6px]"
          :options="fieldCriteriaOptions"
          :model-value="fieldCriteriaState.mandatory.value"
          @update:model-value="handleCriteriaSelection($event, 'mandatory')"
          :multiple="true"
          placeholder="Select Child Field values"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { Switch } from "frappe-ui";
import MultiSelectCombobox from "@/components/frappe-ui/MultiSelectCombobox.vue";

const props = defineProps<{
  parentFieldValues: string[];
}>();

const fieldCriteriaOptions = computed(() => {
  const _options = [{ label: "Any", value: "Any" }];
  props.parentFieldValues.forEach((value) => {
    if (!_options.some((o) => o.value === value)) {
      _options.push({ label: value, value });
    }
  });
  return _options;
});

const fieldCriteriaState = defineModel<{
  display: { enabled: boolean; value: Record<"label" | "value", string>[] };
  mandatory: { enabled: boolean; value: Record<"label" | "value", string>[] };
}>();

function handleCriteriaSelection(
  values: { label: string; value: string }[],
  stateKey: "display" | "mandatory"
) {
  const _values = values.map((v) => v.value);
  debugger;

  if (_values.length > 1) {
    fieldCriteriaState.value[stateKey].value = _values
      .filter((v) => v !== "Any")
      .map((value) => ({
        label: value,
        value,
      }));
  } else if (_values.length === 0) {
    fieldCriteriaState.value[stateKey].value = [{ label: "Any", value: "Any" }];
  } else if (_values.includes("Any") && _values.length === 1) {
    fieldCriteriaState.value[stateKey].value = [{ label: "Any", value: "Any" }];
  } else if (_values.length === 1) {
    fieldCriteriaState.value[stateKey].value = [
      { label: _values[0], value: _values[0] },
    ];
  }
}
</script>

<style scoped></style>
