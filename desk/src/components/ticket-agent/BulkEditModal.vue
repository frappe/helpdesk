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
          :is="getFieldComponent(field.fieldtype)"
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
import { computed, onMounted, onUnmounted, ref, watch } from "vue";

const BULK_UPDATE_METHOD =
  "frappe.desk.doctype.bulk_update.bulk_update.submit_cancel_or_update_docs";

// frappe runs the update inline below this count, enqueues above.
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

let pending: {
  taskId: string;
  toastId: string | number;
  total: number;
} | null = null;

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

const selectedField = computed(
  () =>
    editableFields.value.find((f: any) => f.fieldname === fieldname.value) ??
    null
);

// Its own label would repeat the Combobox; the default placeholder is the raw doctype.
const field = computed(
  () =>
    selectedField.value && {
      ...selectedField.value,
      label: __("Value"),
      placeholder: __("Select {0}", selectedField.value.label),
    }
);

async function submit() {
  if (!fieldname.value) {
    toast.error(__("Select a field"));
    return;
  }
  // Blanking a mandatory field fails `doc.save()` on every ticket.
  if (selectedField.value.reqd && (value.value ?? "") === "") {
    toast.error(__("{0} is required", selectedField.value.label));
    return;
  }

  const docnames = Array.from(props.selections);
  const total = docnames.length;
  const inBackground = total >= BACKGROUND_THRESHOLD;
  const taskId = `bulk-edit-${Math.random().toString(36).slice(2, 10)}`;
  loading.value = true;
  try {
    if (inBackground) $socket.emit("task_subscribe", taskId);
    const failed = await call(BULK_UPDATE_METHOD, {
      doctype: "HD Ticket",
      docnames,
      action: "update",
      data: { [fieldname.value]: value.value ?? null },
      task_id: taskId,
    });
    open.value = false;

    if (inBackground) {
      if (pending) toast.dismiss(pending.toastId);
      const toastId = toast.loading(__("Updating {0} tickets…", total));
      pending = { taskId, toastId, total };
      return;
    }
    // The inline path returns the docnames it could not update.
    if (failed?.length) {
      toast.warning(
        __("Updated {0} of {1} tickets", total - failed.length, total)
      );
    } else {
      toast.success(__("Updated {0} tickets", total));
    }
    emit("success");
  } finally {
    loading.value = false;
  }
}

// Unrelated jobs publish `progress` on the user room too, so match the id.
function onProgress(data: { percent: number; task_id?: string }) {
  if (!pending || data.task_id !== pending.taskId || data.percent < 100) return;
  // Same id replaces the pending toast.
  toast.success(__("Updated {0} tickets", pending.total), {
    id: pending.toastId,
  });
  pending = null;
  emit("success");
}

watch(open, (isOpen) => {
  if (isOpen) fieldname.value = null;
});

watch(fieldname, () => {
  value.value = null;
});

onMounted(() => $socket.on("progress", onProgress));
onUnmounted(() => $socket.off("progress", onProgress));
</script>
