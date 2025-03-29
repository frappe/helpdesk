<template>
  <div class="flex flex-1 flex-col overflow-hidden overflow-y-auto border-b">
    <UniInput2
      v-for="field in fields"
      :key="field.fieldname"
      :field="field"
      :value="ticket[field.fieldname]"
      @change="(data) => update(data.fieldname, data.value)"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import UniInput2 from "../UniInput2.vue";
import { createToast } from "@/utils";
import { Field, FieldValue } from "@/types";
const emit = defineEmits(["update"]);

const props = defineProps({
  ticket: {
    type: Object,
    required: true,
  },
});

const fields = computed(() => {
  return props.ticket.fields;
});

function update(field: Field["fieldname"], value: FieldValue, event = null) {
  if (field === "subject" && value === "") {
    createToast({
      title: "Subject is required",
      icon: "x",
      iconClasses: "text-red-600",
    });
    event.target.value = props.ticket.subject;
    return;
  }
  emit("update", { field, value });
}
</script>
<style scoped>
:deep(.form-control input:not([type="checkbox"])),
:deep(.form-control select),
:deep(.form-control textarea),
:deep(.form-control button) {
  border-color: transparent;
  background: white;
}
:deep(.form-control textarea) {
  field-sizing: content;
}

:deep(.form-control button) {
  gap: 0;
}
:deep(.form-control [type="checkbox"]) {
  margin-left: 9px;
  cursor: pointer;
}

:deep(.form-control button > div) {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

:deep(.form-control button svg) {
  color: white;
  width: 0;
}
</style>
