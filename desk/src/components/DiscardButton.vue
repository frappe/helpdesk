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

const props = withDefaults(
  defineProps<{
    label?: string;
    hideDialog?: boolean;
    title?: string;
    message?: string;
  }>(),
  {
    label: undefined,
    hideDialog: false,
    title: undefined,
    message: undefined,
  }
);

const label = props.label || __("Discard");
const title = props.title || __("Discard?");
const message = props.message || __("Are you sure you want to discard this?");

function handleDiscard() {
  if (props.hideDialog) {
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
        label: __("Confirm"),
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
