<template>
  <Button :label="label" @click="handleDiscard" />
</template>

<script setup lang="ts">
import { globalStore } from "@/stores/globalStore";
import { __ } from "@/translation";
const { $dialog } = globalStore();
const emit = defineEmits<{
  (event: "discard"): void;
}>();

const {
  label = __("Discard"),
  hideDialog = false,
  title = __("Discard?"),
  message = __("Are you sure you want to discard this?"),
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
        label: __("Delete"),
        theme: "red",
        iconLeft: "trash-2",
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
