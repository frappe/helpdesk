<template>
  <div class="h-full flex flex-col">
    <header
      class="flex justify-between mb-8 sticky top-0 z-10 bg-surface-modal"
    >
      <Button
        variant="ghost"
        icon-left="chevron-left"
        label="New Field Dependency"
        size="md"
        @click="() => $emit('update:step', 'fd-list')"
        class="cursor-pointer hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 pl-0 -ml-[5px]"
      />

      <div class="flex gap-2">
        <!-- Switch -->
        <div></div>
        <!-- Actions -->
        <div class="flex gap-1">
          <Button
            label="Save"
            variant="solid"
            size="sm"
            :disabled="!state.selectedParentField"
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
          :options="state.parentFields"
        />
        <FormControl
          v-model="state.selectedChildField"
          label="Child Field"
          placeholder="Select Child Field"
          required
          class="flex-1"
          :disabled="!state.selectedParentField"
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
            <FormControl
              v-model="state.parentSearch"
              placeholder="Search values"
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
                  v-for="value in state.parentFieldValues"
                  :key="value"
                  class="py-2 mb-1 px-2.5 cursor-pointer rounded flex justify-between items-center hover:bg-surface-gray-1"
                  :class="{
                    'bg-surface-gray-2 hover:bg-surface-gray-3':
                      state.currentParentSelection === value,
                  }"
                  @click="handleParentValueClick(value)"
                >
                  <span class="text-base text-ink-gray-6">{{ value }}</span>
                  <LucideChevronRight class="h-4 w-4 text-ink-gray-6" />
                </li>
              </ul>
            </div>
          </div>
        </div>
        <!-- right box -->
        <div class="flex-1 flex flex-col gap-1.5">
          <span class="block text-xs text-ink-gray-5 pl-1.5">
            Select child field value
          </span>
          <div class="border flex-1 rounded-r p-2 flex flex-col gap-2">
            <FormControl
              v-model="state.childSearch"
              placeholder="Search values"
              type="text"
              class="w-full"
            >
              <template #prefix>
                <LucideSearch class="h-4 w-4 text-gray-500" />
              </template>
            </FormControl>
            <div class="flex-1 overflow-y-auto hide-scrollbar basis-0">
              <template v-if="state.currentParentSelection">
                <ul>
                  <li
                    v-for="value in state.childFieldValues"
                    :key="value"
                    class="py-2 mb-1 px-2.5 cursor-pointer rounded flex items-center hover:bg-surface-gray-1"
                    :class="{
                      'bg-surface-gray-2 hover:bg-surface-gray-3':
                        isChildValueSelected(value),
                    }"
                    @click="handleChildValueClick(value)"
                  >
                    <input
                      type="checkbox"
                      :checked="isChildValueSelected(value)"
                      readonly
                      class="mr-2"
                    />
                    <span class="text-base text-ink-gray-6">{{ value }}</span>
                  </li>
                </ul>
              </template>
              <template v-else>
                <div
                  class="flex flex-col items-center justify-center h-full text-ink-gray-4 text-sm"
                >
                  Please select a parent value first
                </div>
              </template>
            </div>
          </div>
        </div>
      </div>
    </form>
  </div>
</template>

<script setup>
import { call, createResource } from "frappe-ui";
import FormControl from "frappe-ui/src/components/FormControl/FormControl.vue";
import { reactive, watch } from "vue";

const state = reactive({
  selectedParentField: "",
  selectedChildField: "",
  parentFields: [],
  childFields: [],

  parentFieldValues: [],
  childFieldValues: [],

  currentParentSelection: "",
  childSelections: {}, // Initial value is a Set

  parentSearch: "",
  childSearch: "",
});

const fields = createResource({
  url: "helpdesk.api.ticket_meta.get_fields_meta",
  auto: true,
  params: {
    doctype: "HD Ticket",
    fieldtypes: ["Select", "Link"],
  },
  //   cache: ["Fields", "field_dependency"],
  transform: (data) => {
    state.parentFields = data.map((field) => ({
      label: field.label,
      value: field.fieldname,
      options: field.options || [],
      type: field.fieldtype,
    }));
    return data;
  },
});

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

async function handleFieldValues(fieldname, isParentField) {
  if (!fieldname) return [];

  const field = isParentField
    ? state.parentFields.find((f) => f.value === fieldname)
    : state.childFields.find((f) => f.value === fieldname);
  if (!field) return [];

  if (isParentField) {
    state.selectedChildField = ""; // Reset child field when parent changes
    state.childFields = state.parentFields.filter((f) => f.value !== fieldname);
    state.childFieldValues = [];
    state.currentParentSelection = ""; // Reset current parent selection
    state.childSelections = {}; // Reset child selections for new parent
  }

  if (field.type === "Select") {
    return field.options.split("\n");
  } else if (field.type === "Link") {
    let options = await call("frappe.client.get_list", {
      doctype: field.options,
      fields: ["name"],
      limit_page_length: 999,
    });
    return options.map((o) => o.name);
  }
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

function handleSubmit() {
  // Handle form submission
  console.log("Parent Field:", state.selectedParentField);
  console.log("Child Field:", state.selectedChildField);
}
</script>

<style scoped></style>
