<template>
  <template v-if="customFieldMeta.length">
    <div v-for="field in values" :key="field.fieldname" class="space-y-1">
      <div class="text-xs text-gray-600">
        {{ fieldMeta[field.fieldname].label }}
      </div>
      <SearchComplete
        v-if="
          fieldMeta[field.fieldname].fieldtype == 'Link' &&
          fieldMeta[field.fieldname].options
        "
        :value="field.value"
        :doctype="fieldMeta[field.fieldname].options"
        @change="
          (v) => $emit('change', { fieldname: field.fieldname, value: v.value })
        "
      />

      <SearchComplete
        v-else-if="
          fieldMeta[field.fieldname].fieldtype === 'Link' &&
          fieldMeta[field.fieldname].fetch_options_from == 'DocType'
        "
        :value="field.value"
        :doctype="fieldMeta[field.fieldname].doc_type"
        @change="
          (v) => $emit('change', { fieldname: field.fieldname, value: v.value })
        "
      />
      <Autocomplete
        v-else-if="fieldMeta[field.fieldname].fieldtype === 'Select'"
        placeholder="Select an option"
        :options="selectOptions(fieldMeta[field.fieldname].options)"
        :value="field.value"
        @change="
          (v) => $emit('change', { fieldname: field.fieldname, value: v.value })
        "
      />
      <Autocomplete
        v-else-if="fieldMeta[field.fieldname].fetch_options_from === 'API'"
        placeholder="Select an option"
        :options="serverScriptOptions[field.fieldname]"
        :value="field.value"
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
const fieldMeta = computed(() => {
  const meta = {};
  customFieldMeta.value.forEach((field) => {
    meta[field.fieldname] = field;
  });
  return meta;
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
