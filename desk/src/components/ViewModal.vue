<template>
  <Dialog v-model:open="viewDialog.show" :title="modalInfo.modalTitle">
    <template #default>
      <div class="mb-1.5 block text-base text-ink-gray-5">View Name</div>
      <div class="flex gap-2">
        <IconPicker v-model="view.icon" v-slot="{ togglePopover }">
          <Button
            size="md"
            class="flex size-10 text-3xl leading-none"
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

      <!-- Layout picker — applies to Create, Duplicate, and Edit so
           every dialog touching the view doc surfaces the same control.
           For Edit, the current view's type pre-fills it (see
           viewDialog.view.type set by the parent on open). -->
      <div class="mt-4 mb-1.5 block text-base text-ink-gray-5">
        {{ __("Layout") }}
      </div>
      <div class="inline-flex rounded-md bg-surface-gray-2 p-0.5">
        <button
          v-for="opt in layoutOptions"
          :key="opt.value"
          type="button"
          class="flex items-center gap-1.5 rounded px-3 py-1 text-sm transition"
          :class="
            view.type === opt.value
              ? 'bg-surface-white text-ink-gray-9 shadow-sm'
              : 'text-ink-gray-6 hover:text-ink-gray-8'
          "
          @click="view.type = opt.value"
        >
          <FeatherIcon :name="opt.icon" class="h-3.5 w-3.5" />
          {{ opt.label }}
        </button>
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
import { Dialog, FeatherIcon } from "frappe-ui";
import IconPicker from "@/components/IconPicker.vue";
import { computed } from "vue";
import { __ } from "@/translation";

let viewDialog = defineModel();

const view = ref({
  label: viewDialog.value.view.label || "",
  icon: viewDialog.value.view.icon || "",
  name: viewDialog.value.view.name || "",
  type: viewDialog.value.view.type || "list",
});

const layoutOptions = [
  { value: "list", label: __("List"), icon: "align-justify" },
  { value: "kanban", label: __("Kanban"), icon: "columns" },
];

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
