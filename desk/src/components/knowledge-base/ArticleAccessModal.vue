<template>
  <Dialog v-model:open="show" :title="title">
    <div class="flex flex-col gap-4">
      <div class="flex flex-col gap-2">
        <span class="text-p-sm text-ink-gray-6">
          {{ __("General access") }}
        </span>
        <Select
          v-model="access"
          class="w-full"
          size="md"
          :options="accessOptions"
          :placeholder="__('Mixed')"
        />
        <slot :access="access" />
      </div>

      <div class="flex justify-end">
        <Button
          variant="solid"
          :label="actionLabel || __('Publish')"
          :disabled="!access || (requireChange && access === visibility)"
          @click="publish"
        />
      </div>
    </div>
  </Dialog>
</template>

<script setup lang="ts">
import { Button, Dialog, Select } from "frappe-ui";
import { computed, ref, watch } from "vue";
import { __ } from "@/translation";

// A null `visibility` is a category whose articles differ.
const props = defineProps<{
  title: string;
  visibility: string | null;
  actionLabel?: string;
  requireChange?: boolean;
}>();
const emit = defineEmits<{ publish: [visibility: string] }>();
const show = defineModel<boolean>({ default: false });

const accessOptions = computed(() => [
  {
    value: "Agents only",
    label: __("Accessible to agents only"),
    icon: "lucide-lock",
  },
  {
    value: "Customers only",
    label: __("Accessible to customers only"),
    icon: "lucide-building-2",
  },
  {
    value: "Public",
    label: __("Accessible to everyone"),
    icon: "lucide-globe",
  },
]);

const access = ref(props.visibility);

watch(show, (open) => {
  if (open) access.value = props.visibility;
});

function publish() {
  emit("publish", access.value!);
  show.value = false;
}
</script>
