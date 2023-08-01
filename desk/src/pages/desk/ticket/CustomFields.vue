<template>
  <template v-if="customFieldMeta.length">
    <div
      v-for="field in customFieldMeta"
      :key="field.fieldname"
      class="space-y-1"
    >
      <div class="text-xs text-gray-600">
        {{ field.label }}
        <span v-if="field.reqd" class="text-red-500">*</span>
      </div>
      <SearchComplete
        v-if="field.fieldtype == 'Link' && field.options"
        :value="fieldValues[field.fieldname]"
        :doctype="field.options"
        @change="
          (v) => $emit('change', { fieldname: field.fieldname, value: v.value })
        "
      />

      <SearchComplete
        v-else-if="
          field.fieldtype === 'Link' && field.fetch_options_from == 'DocType'
        "
        :value="fieldValues[field.fieldname]"
        :doctype="field.doc_type"
        @change="
          (v) => $emit('change', { fieldname: field.fieldname, value: v.value })
        "
      />
      <Autocomplete
        v-else-if="field.fieldtype === 'Select'"
        placeholder="Select an option"
        :options="
          field.options.split('\n').map((o) => ({ label: o, value: o }))
        "
        :value="fieldValues[field.fieldname]"
        @change="
          (v) => $emit('change', { fieldname: field.fieldname, value: v.value })
        "
      />
      <Autocomplete
        v-else-if="field.fetch_options_from === 'API'"
        placeholder="Select an option"
        :options="serverScriptOptions[field.fieldname]"
        :value="fieldValues[field.fieldname]"
        @change="
          (v) => $emit('change', { fieldname: field.fieldname, value: v.value })
        "
      />
    </div>
  </template>
</template>

<script setup>
import SearchComplete from "@/components/SearchComplete.vue";
import { Autocomplete, createDocumentResource, call } from "frappe-ui";
import { ref, computed } from "vue";

const props = defineProps({ template: String, values: Object });
defineEmits(["change"]);

const customFieldMeta = ref([]);
const template = createDocumentResource({
  doctype: "HD Ticket Template",
  name: props.template,
  fields: ["fields"],
  auto: true,
  onSuccess: () => {
    customFieldMeta.value = template.doc.fields;
    fetchOptionsFromServerScript();
  },
});
const fieldValues = computed(() => {
  const values = {};
  props.values.forEach((v) => {
    values[v.fieldname] = v.value;
  });
  return values;
});

const serverScriptOptions = ref({});
function fetchOptionsFromServerScript() {
  customFieldMeta.value.forEach((field) => {
    if (field.fetch_options_from === "API") {
      call(field.api_method).then((data) => {
        const options = data.map((o) => ({
          label: o,
          value: o,
        }));
        serverScriptOptions[field.fieldname] = options;
      });
    }
  });
}
</script>
