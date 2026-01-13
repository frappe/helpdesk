<template>
  <Button :label="label" @click="handleDiscard" />
</template>

<script setup lang="ts">
import { globalStore } from "@/stores/globalStore";
const { $dialog } = globalStore();
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
  $dialog({
    title: title,
    message: message,
    onConfirm: ({ hideDialog }: { hideDialog: Function }) => {
      hideDialog();
    },
    actions: [
      {
        label: "Confirm",
        variant: "solid",
        onClick(close: Function) {
          emit("discard");
          close();
        },
      },
    ],
  });
}
</script>
