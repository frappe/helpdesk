<template>
  <Dialog v-model:open="viewDialog.show" :title="modalInfo.modalTitle">
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
import { __ } from "@/translation";
import { isEmoji } from "@/utils";
import { Dialog } from "frappe-ui";
import { IconPicker } from "frappe-ui/icons";
import { computed, ref } from "vue";

let viewDialog = defineModel();

const view = ref({
  label: viewDialog.value.view.label || "",
  icon: viewDialog.value.view.icon || "",
  name: viewDialog.value.view.name || "",
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
