<template>
  <Dialog v-model:open="open" :title="__('Assign')">
    <template #default>
      <AssignTo v-model="assignees" hide-label />
    </template>
    <template #actions>
      <div class="flex items-center justify-end gap-2">
        <Button :label="__('Cancel')" @click="open = false" />
        <Button
          variant="solid"
          :loading="loading"
          :disabled="!assignees.length"
          :label="__('Assign {0} tickets', selections.size)"
          @click="submit"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import AssignTo from "@/components/ticket-agent/AssignTo.vue";
import { __ } from "@/translation";
import { Button, call, Dialog, toast } from "frappe-ui";
import { ref, watch } from "vue";

const ASSIGN_METHOD = "frappe.desk.form.assign_to.add_multiple";

const open = defineModel<boolean>();

const props = defineProps<{
  selections: Set<string>;
}>();
const emit = defineEmits<{
  (e: "success"): void;
}>();

const assignees = ref<string[]>([]);
const loading = ref(false);

async function submit() {
  if (!assignees.value.length) return;
  const ticketIds = Array.from(props.selections);
  loading.value = true;
  try {
    // `add_multiple` reads the raw form_dict, so the lists go as JSON strings.
    await call(ASSIGN_METHOD, {
      doctype: "HD Ticket",
      name: JSON.stringify(ticketIds),
      assign_to: JSON.stringify(assignees.value),
    });
    open.value = false;
    toast.success(__("Assigned {0} tickets", ticketIds.length));
    emit("success");
  } finally {
    loading.value = false;
  }
}

watch(open, (isOpen) => {
  if (isOpen) assignees.value = [];
});
</script>
