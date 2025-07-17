<template>
  <Dialog v-model="showDialog" :options="{ title }" @close="closeDialog">
    <template #body-content>
      <div class="space-y-4">
        <p class="text-p-base text-gray-800" v-if="message" v-html="message" />
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
    onConfirm: {
      type: Function,
      default: null,
    },
    onCancel: {
      type: Function,
      default: null,
    },
  },
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
      this.showDialog = true;
    },
    closeDialog() {
      this.hide();
      this.onCancel?.();
    },
    hide() {
      this.showDialog = false;
    },
  },
};
</script>
