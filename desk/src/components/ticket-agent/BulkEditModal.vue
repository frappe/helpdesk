<template>
  <Dialog v-model:open="open" :title="__('Edit')">
    <template #default>
      <div class="flex flex-col gap-4">
        <Combobox
          v-model="fieldname"
          :label="__('Field')"
          :options="fieldOptions"
          :placeholder="__('Select a field')"
        />
        <component
          v-if="field"
          :is="control"
          :key="fieldname"
          :field="field"
          :model-value="value"
          @update:model-value="(newValue: any) => (value = newValue)"
        />
      </div>
    </template>
    <template #actions>
      <div class="flex items-center justify-end gap-2">
        <Button :label="__('Cancel')" @click="open = false" />
        <Button
          variant="solid"
          :loading="loading"
          :disabled="!fieldname"
          :label="__('Update {0} tickets', selections.size)"
          @click="submit"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { globalStore } from "@/stores/globalStore";
import { getMeta } from "@/stores/meta";
import { __ } from "@/translation";
import { getFieldComponent } from "@framework/ui/fields";
import { Button, call, Combobox, Dialog, toast } from "frappe-ui";
import { computed, ref, watch } from "vue";

const BULK_UPDATE_METHOD =
  "frappe.desk.doctype.bulk_update.bulk_update.submit_cancel_or_update_docs";

// frappe runs the update inline below this count and enqueues it above.
const BACKGROUND_THRESHOLD = 20;

// Fieldtypes that hold no value, so there is nothing to bulk set.
const NO_VALUE_TYPES = new Set([
  "Section Break",
  "Column Break",
  "Tab Break",
  "Fold",
  "Heading",
  "HTML",
  "Image",
  "Button",
  "Table",
  "Table MultiSelect",
  "Read Only",
]);

const open = defineModel<boolean>();

const props = defineProps<{
  selections: Set<string>;
}>();
const emit = defineEmits<{
  (e: "success"): void;
}>();

const { $socket } = globalStore();
const { getFields } = getMeta("HD Ticket");

const fieldname = ref<string | null>(null);
const value = ref<any>(null);
const loading = ref(false);

const editableFields = computed(() =>
  getFields().filter(
    (field: any) =>
      field.fieldname &&
      !NO_VALUE_TYPES.has(field.fieldtype) &&
      !field.hidden &&
      !field.read_only &&
      !field.is_virtual
  )
);

const fieldOptions = computed(() =>
  editableFields.value
    .map((field: any) => ({ label: __(field.label), value: field.fieldname }))
    .sort((a, b) => a.label.localeCompare(b.label))
);

const field = computed(() =>
  editableFields.value.find((f: any) => f.fieldname === fieldname.value)
);

// The fieldtype registry picks the control; the docfield doubles as its meta.
const control = computed(() =>
  field.value ? getFieldComponent(field.value.fieldtype) : null
);

async function submit() {
  if (!fieldname.value) return;
  const docnames = Array.from(props.selections);
  loading.value = true;
  try {
    await call(BULK_UPDATE_METHOD, {
      doctype: "HD Ticket",
      docnames,
      action: "update",
      data: { [fieldname.value]: value.value ?? null },
    });
    open.value = false;
    if (docnames.length < BACKGROUND_THRESHOLD) {
      toast.success(__("Updated {0} tickets", docnames.length));
      emit("success");
    } else {
      toast.success(
        __("Updating {0} tickets in the background", docnames.length)
      );
      reloadWhenDone();
    }
  } finally {
    loading.value = false;
  }
}

/** The enqueued job reports through `frappe.publish_progress` on the user room. */
function reloadWhenDone() {
  const onProgress = ({ percent }: { percent: number }) => {
    if (percent < 100) return;
    $socket.off("progress", onProgress);
    toast.success(__("Bulk edit completed"));
    emit("success");
  };
  $socket.on("progress", onProgress);
}

watch(open, (isOpen) => {
  if (!isOpen) return;
  fieldname.value = null;
  value.value = null;
});

watch(fieldname, () => {
  value.value = null;
});
</script>
