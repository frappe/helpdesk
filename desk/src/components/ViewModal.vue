<template>
  <Dialog v-model:open="viewDialogConfig.show" :title="modalInfo.modalTitle">
    <template #default>
<<<<<<< HEAD
      <div class="mb-1.5 block text-base text-ink-gray-5">View Name</div>
      <div class="flex gap-2">
        <IconPicker v-model="view.icon" v-slot="{ togglePopover }">
          <Button
            size="md"
            class="flex size-8 text-3xl leading-none"
            :label="view.icon"
            @click="togglePopover"
=======
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
>>>>>>> 8fa03b64 (fix(views): use icons instead of emojis)
          />
        </div>
        <div>
          <div class="mb-1.5 text-base text-ink-gray-5">{{ __("Icon") }}</div>
          <div class="flex items-center gap-2">
            <div
              v-if="currentIsEmoji"
              class="grid size-7 shrink-0 place-items-center rounded bg-surface-gray-3 text-base leading-none"
              :title="__('Current icon')"
            >
              {{ view.icon }}
            </div>
            <IconPicker
              v-model="pickerIcon"
              :max-icons="1000"
              class="flex-1"
              :placeholder="
                currentIsEmoji
                  ? __('Replace with an icon...')
                  : __('Select an icon...')
              "
            />
          </div>
        </div>
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
import { isCustomerPortal, isEmoji } from "@/utils";
import { Dialog } from "frappe-ui";
import { IconPicker } from "frappe-ui/icons";
import { computed, ref } from "vue";

let viewDialogConfig = defineModel();

const { isManager } = useAuthStore();

const view = ref({
  label: viewDialogConfig.value.view.label || "",
  icon: viewDialogConfig.value.view.icon || "",
  name: viewDialogConfig.value.view.name || "",
  pinned: false,
  public: false,
});

// frappe-ui's IconPicker is lucide-only. Legacy views may store an emoji, which
// the picker would otherwise echo as raw text. Hide non-lucide values from the
// picker (showing the placeholder) while keeping the stored icon intact, so a
// no-op edit preserves the emoji and picking a lucide icon migrates it.
const currentIsEmoji = computed(() => isEmoji(view.value.icon));

const pickerIcon = computed({
  get: () => {
    const icon = view.value.icon;
    if (!icon || isEmoji(icon)) return "";
    return icon.replace(/^lucide-/, "");
  },
  set: (value) => {
    view.value.icon = value || "";
  },
});

const isCreateMode = computed(() => modalInfo.value.action === "create");

// Only managers can publish views, and the customer portal has no public views.
const canMakePublic = computed(() => isManager && !isCustomerPortal.value);

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
