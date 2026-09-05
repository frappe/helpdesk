<template>
  <Dialog
    v-model="show"
    :options="{
      title: isRename ? 'Rename view' : 'Save as new view',
      actions: [
        {
          label: isRename ? 'Save' : 'Create',
          variant: 'solid',
          disabled: !label.trim(),
          onClick: () => emit('submit'),
        },
      ],
    }"
  >
    <template #body-content>
      <FormControl
        v-model="label"
        type="text"
        label="Name"
        placeholder="My open tickets"
        autocomplete="off"
        @keyup.enter="label.trim() && emit('submit')"
      />
      <div class="mt-4">
        <div class="mb-1.5 text-base text-ink-gray-5">Icon</div>
        <div class="flex items-center gap-2">
          <!-- Existing views mostly carry an emoji (that is what the desk's picker
               wrote), which the icon list can't show — so it previews beside it. -->
          <div
            v-if="isEmojiIcon"
            class="grid size-7 shrink-0 place-items-center rounded bg-surface-gray-3 text-base leading-none"
            title="Current icon"
          >
            {{ icon }}
          </div>
          <IconPicker
            v-model="icon"
            :max-icons="1000"
            class="flex-1"
            :placeholder="
              isEmojiIcon ? 'Replace with an icon...' : 'Select an icon...'
            "
          />
        </div>
      </div>
      <p v-if="!isRename" class="mt-4 text-p-sm text-ink-gray-6">
        Saves the filters, sort order and columns currently on screen.
      </p>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
// Create/rename dialog for a saved view. The desk's ViewModal also offers "Pin to
// sidebar" and "Make it public"; neither applies here — this portal has no sidebar,
// and the desk itself hides "public" outside the agent view (`isManager &&
// !isCustomerPortal`). So a customer's view is just a name over the current layout.
import { Dialog, FormControl } from "frappe-ui";
// Reads the lucide sprite the studio renderer's `spritePlugin` injects — verified to
// carry the full set (1713 symbols), not just icons the bundle happens to reference.
import { IconPicker } from "frappe-ui/icons";
import { computed } from "vue";

const props = defineProps<{ modelValue: any }>();
const emit = defineEmits<{
  (e: "update:modelValue", value: any): void;
  (e: "submit"): void;
}>();

const show = computed({
  get: () => Boolean(props.modelValue?.show),
  set: (value) =>
    emit("update:modelValue", { ...props.modelValue, show: value }),
});

const label = computed({
  get: () => props.modelValue?.label || "",
  set: (value) =>
    emit("update:modelValue", { ...props.modelValue, label: value }),
});

const icon = computed({
  get: () => props.modelValue?.icon || "",
  set: (value) =>
    emit("update:modelValue", { ...props.modelValue, icon: value }),
});

const isRename = computed(() => props.modelValue?.mode === "rename");
const isEmojiIcon = computed(() =>
  /\p{Extended_Pictographic}/u.test(icon.value)
);
</script>
