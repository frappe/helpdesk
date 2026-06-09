<template>
  <Dialog v-model:open="isOpen" :title="title" @close="closeDialog">
    <template #default>
      <div class="space-y-4">
        <p
          class="text-p-base text-ink-gray-8"
          v-if="message"
          v-html="message"
        />
      </div>
    </template>
    <template #actions>
      <Button
        class="w-full"
        label="Confirm"
        variant="solid"
        :loading="isLoading"
        @click="onConfirm"
      />
    </template>
  </Dialog>
</template>
<script>
import { Button, Dialog } from "frappe-ui";

export default {
  name: "ConfirmDialog",
  props: {
    title: {
      type: String,
    },
    message: {
      type: String,
    },
    // Optional v-model; when absent, visibility falls back to the internal
    // state (open on mount), preserving the `v-if` + `show()`/`hide()` mode.
    modelValue: {
      type: Boolean,
      default: undefined,
    },
    onConfirm: {
      type: Function,
      default: null,
    },
    onCancel: {
      type: Function,
      default: null,
    },
  },
  emits: ["update:modelValue"],
  expose: ["show", "hide"],
  components: {
    Dialog,
    Button,
  },
  data() {
    return {
      showDialog: true,
      isLoading: false,
    };
  },
  computed: {
    isOpen: {
      get() {
        return this.modelValue !== undefined
          ? this.modelValue
          : this.showDialog;
      },
      set(value) {
        this.showDialog = value;
        this.$emit("update:modelValue", value);
      },
    },
  },
  methods: {
    async handleConfirmation() {
      if (this.isLoading) return;
      this.isLoading = true;
      try {
        if (this.onConfirm) {
          await this.onConfirm({
            hideDialog: this.hide,
          });
        }
        this.hide();
      } catch (error) {
        console.error("Error in confirmation:", error);
      } finally {
        this.isLoading = false;
      }
    },
    show() {
      this.isOpen = true;
    },
    closeDialog() {
      this.hide();
      this.onCancel?.();
    },
    hide() {
      this.isOpen = false;
    },
  },
};
</script>
