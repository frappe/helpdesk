<template>
  <Dialog
    v-model="viewDialog.show"
    :options="{
      title: modalInfo.modalTitle,
    }"
  >
    <template #body-content>
      <div class="mb-1.5 block text-base text-ink-gray-5">View Name</div>
      <div class="flex gap-2">
        <IconPicker v-model="view.icon" v-slot="{ togglePopover }">
          <Button
            size="md"
            class="flex size-8 text-2xl leading-none"
            :label="view.icon"
            @click="togglePopover"
          />
        </IconPicker>
        <FormControl
          class="flex-1"
          size="md"
          type="text"
          placeholder="My Open Tickets"
          v-model="view.label"
        />
      </div>
    </template>
    <template #actions>
      <Button
        :label="modalInfo.buttonLabel"
        variant="solid"
        @click="emit('update', view, modalInfo.action)"
        class="w-full"
      />
    </template>
  </Dialog>
</template>

<script setup>
import { ref } from "vue";
import { Dialog } from "frappe-ui";
import IconPicker from "@/components/IconPicker.vue";
import { computed } from "vue";

let viewDialog = defineModel();

const view = ref({
  label: viewDialog.value.view.label || "",
  icon: viewDialog.value.view.icon || "",
  name: viewDialog.value.view.name || "",
});

const modalInfo = computed(() => {
  return {
    modalTitle:
      viewDialog.value.mode === "edit"
        ? "Edit View"
        : viewDialog.value.mode === "duplicate"
        ? "Duplicate View"
        : "Create View",
    buttonLabel:
      viewDialog.value.mode === "edit"
        ? "Update"
        : viewDialog.value.mode === "duplicate"
        ? "Duplicate"
        : "Create",
    action:
      viewDialog.value.mode === "edit"
        ? "update"
        : viewDialog.value.mode === "duplicate"
        ? "duplicate"
        : "create",
  };
});

const emit = defineEmits(["update"]);
</script>
