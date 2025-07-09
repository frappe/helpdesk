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
          <Button label="Save" variant="solid" size="sm" />
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
          v-model="state.parentField"
          label="Parent Field"
          placeholder="Select Parent Field"
          required
          class="flex-1"
          type="select"
          :options="state.parentFieldOptions"
        />
        <FormControl
          v-model="state.childField"
          label="Child Field"
          placeholder="Select Child Field"
          required
          class="flex-1"
          :disabled="!state.parentField"
          type="select"
          :options="state.childFieldOptions"
        />
      </div>
      <!-- Value Selection -->
      <div class="flex w-full flex-1 justify-between h-full">
        <!-- left box -->
        <div class="flex-1 flex flex-col gap-1.5">
          <span class="block text-xs text-ink-gray-5">
            Select parent field value
          </span>
          <div class="border flex-1 border-r-0 rounded-l p-2">
            <FormControl
              v-model="state.parentSearch"
              placeholder="Search values"
              type="text"
              class="w-full mb-2"
            >
              <template #prefix>
                <LucideSearch class="h-4 w-4 text-gray-500" />
              </template>
            </FormControl>
            {{ childFieldComponent }}
          </div>
        </div>
        <!-- right box -->
        <div class="flex-1 flex flex-col gap-1.5">
          <span class="block text-xs text-ink-gray-5 pl-1.5">
            Select child field value
          </span>
          <div class="border flex-1 rounded-r p-2">
            <FormControl
              v-model="state.childSearch"
              placeholder="Search values"
              type="text"
              class="w-full mb-2"
            >
              <template #prefix>
                <LucideSearch class="h-4 w-4 text-gray-500" />
              </template>
            </FormControl>
          </div>
        </div>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { createResource } from "frappe-ui";
import FormControl from "frappe-ui/src/components/FormControl/FormControl.vue";
import { computed, reactive } from "vue";

const state = reactive({
  parentField: "",
  childField: "",
  parentFieldOptions: [],
  childFieldOptions: [],
  parentSearch: "",
  childSearch: "",
  currentParentSelection: "",
  currentChildSelection: [],
});

const fields = createResource({
  url: "helpdesk.api.ticket_meta.get_fields_meta",
  auto: true,
  cache: ["dsdf", "sdfdsf"],
  params: {
    doctype: "HD Ticket",
    fieldtypes: ["Select", "Link"],
  },
  onData: (data) => {
    state.parentFieldOptions = data.map((field) => ({
      label: field.label,
      value: field.fieldname,
      options: field.options || [],
      type: field.fieldtype,
    }));
    return data;
  },
  //   onSuccess: (data) => {
  //     state.parentFieldOptions = data.map((field) => ({
  //       label: field.label,
  //       value: field.fieldname,
  //       options: field.options || [],
  //       type: field.fieldtype,
  //     }));
  //     return data;
  //   },
});

const childFieldComponent = computed(() => {
  const field = state.parentFieldOptions.find(
    (f) => f.value === state.parentField
  );
  if (!field) return null;
  state.childFieldOptions = state.parentFieldOptions.filter(
    (o) => o.value != state.parentField
  );
  //   if (field.type === "Select") {
  //     let options = field.options.split("\n");
  //     state.childFieldOptions = options;
  //   }
});

function handleSubmit() {
  // Handle form submission
  console.log("Parent Field:", state.parentField);
  console.log("Child Field:", state.childField);
}
</script>

<style scoped></style>
