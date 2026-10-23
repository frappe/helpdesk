<template>
  <Dialog v-model:open="viewDialogConfig.show" :title="modalInfo.modalTitle">
    <template #default>
      <div class="flex flex-col gap-4">
        <div>
          <div class="mb-1.5 text-base text-ink-gray-5">
            {{ __("Name") }} <span class="text-ink-red-3">*</span>
          </div>
          <FormControl
            size="sm"
            type="text"
            placeholder="My Open Tickets"
            v-model="view.label"
          />
        </div>
        <ViewIconField v-model="view.icon" />
        <!-- A view is either pinned (private, in "Private Views") or public (in
        "Public Views") - never both - so checking one disables the other. -->
        <div v-if="isCreateMode" class="grid grid-cols-2 gap-2">
          <FormControl
            type="checkbox"
            :label="__('Pin to sidebar')"
            v-model="view.pinned"
            :disabled="Boolean(view.public)"
          />
          <FormControl
            v-if="canMakePublic"
            type="checkbox"
            :label="__('Make it public')"
            v-model="view.public"
            :disabled="Boolean(view.pinned)"
          />
        </div>
      </div>
    </template>
    <template #actions>
      <Button
        :label="modalInfo.buttonLabel"
        variant="solid"
        :disabled="!view.label.trim()"
        @click="emit('update', view, modalInfo.action)"
        class="w-full"
      />
    </template>
  </Dialog>
</template>

<script setup>
import { useAuthStore } from "@/stores/auth";
import { __ } from "@/translation";
import ViewIconField from "@helpdesk/shared/ViewIconField.vue";
import { Dialog } from "frappe-ui";
import { computed, ref } from "vue";

let viewDialogConfig = defineModel();

const { isManager } = useAuthStore();

// New views start with the ticket icon preselected - it is also what an
// empty icon falls back to when rendering.
const isCreate = !["edit", "duplicate"].includes(viewDialogConfig.value.mode);

const view = ref({
  label: viewDialogConfig.value.view.label || "",
  icon: viewDialogConfig.value.view.icon || (isCreate ? "ticket" : ""),
  name: viewDialogConfig.value.view.name || "",
  pinned: false,
  public: false,
});

const isCreateMode = computed(() => modalInfo.value.action === "create");

// Only managers can publish views.
const canMakePublic = computed(() => isManager);

const modalInfo = computed(() => {
  return {
    modalTitle:
      viewDialogConfig.value.mode === "edit"
        ? "Edit View"
        : viewDialogConfig.value.mode === "duplicate"
        ? "Duplicate View"
        : "Create View",
    buttonLabel:
      viewDialogConfig.value.mode === "edit"
        ? "Update"
        : viewDialogConfig.value.mode === "duplicate"
        ? "Duplicate"
        : "Create",
    action:
      viewDialogConfig.value.mode === "edit"
        ? "update"
        : viewDialogConfig.value.mode === "duplicate"
        ? "duplicate"
        : "create",
  };
});

const emit = defineEmits(["update"]);
</script>
