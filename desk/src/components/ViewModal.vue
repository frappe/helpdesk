<template>
  <Dialog
    v-model="viewDialog.show"
    :options="{
      title: modalInfo.modalTitle,
    }"
  >
    <template #body-content>
      <div class="mb-1.5 block text-base text-ink-gray-5">
        {{ __("View Name") }}
      </div>
      <div class="flex gap-2">
        <IconPicker v-model="view.icon" v-slot="{ togglePopover }">
          <Button
            size="md"
            class="flex size-10 text-2xl leading-none"
            :label="view.icon"
            @click="togglePopover"
          />
        </IconPicker>
        <FormControl
          class="flex-1"
          size="md"
          type="text"
          :placeholder="__('My Open Tickets')"
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
import { __ } from "@/translation";

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
        ? __("Edit View")
        : viewDialog.value.mode === "duplicate"
        ? __("Duplicate View")
        : __("Create View"),
    buttonLabel:
      viewDialog.value.mode === "edit"
        ? __("Update")
        : viewDialog.value.mode === "duplicate"
        ? __("Duplicate")
        : __("Create"),
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
