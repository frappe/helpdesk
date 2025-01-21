<template>
  <Button :label="label" @click="handleDiscard" />
</template>

<script setup lang="ts">
import { confirmDialog } from "frappe-ui";

const emit = defineEmits<{
  (event: "discard"): void;
}>();

const {
  label = "Discard",
  hideDialog = false,
  title = "Discard?",
  message = "Are you sure you want to discard this?",
} = defineProps<{
  label?: string;
  hideDialog?: boolean;
  title?: string;
  message?: string;
}>();

function handleDiscard() {
  if (hideDialog) {
    emit("discard");
    return;
  }
  confirmDialog({
    title: title,
    message: message,
    onConfirm: ({ hideDialog }: { hideDialog: Function }) => {
      emit("discard");
      hideDialog();
    },
  });
}
</script>
