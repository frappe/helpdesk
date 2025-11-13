<template>
  <Button :label="displayLabel" @click="handleDiscard" />
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useTranslation } from "@/composables/useTranslation";
import { globalStore } from "@/stores/globalStore";

// Reactive translations
const tDiscard = useTranslation("Discard");
const tDiscardQuestion = useTranslation("Discard?");
const tAreYouSure = useTranslation("Are you sure you want to discard this?");
const tConfirm = useTranslation("Confirm");

const { $dialog } = globalStore();
const emit = defineEmits<{
  (event: "discard"): void;
}>();

const props = withDefaults(defineProps<{
  label?: string;
  hideDialog?: boolean;
  title?: string;
  message?: string;
}>(), {
  label: "",
  hideDialog: false,
  title: "",
  message: "",
});

// Use translations if no custom values provided
const displayLabel = computed(() => props.label || tDiscard.value);
const displayTitle = computed(() => props.title || tDiscardQuestion.value);
const displayMessage = computed(() => props.message || tAreYouSure.value);

function handleDiscard() {
  if (props.hideDialog) {
    emit("discard");
    return;
  }
  $dialog({
    title: displayTitle.value,
    message: displayMessage.value,
    onConfirm: ({ hideDialog }: { hideDialog: Function }) => {
      hideDialog();
    },
    actions: [
      {
        label: tConfirm.value,
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
