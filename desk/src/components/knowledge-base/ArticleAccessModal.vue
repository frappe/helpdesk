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
          :label="actionLabel"
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
import { categoryAccess } from "@helpdesk/shared/settings/categoryAccess.ts";
import { __ } from "@/translation";

// null: the category's articles differ in access.
const props = defineProps<{
  title: string;
  visibility: string | null;
  actionLabel: string;
  requireChange?: boolean;
}>();
const emit = defineEmits<{ publish: [visibility: string] }>();
const show = defineModel<boolean>({ default: false });

const accessOptions = computed(() => {
  const meta = categoryAccess();
  return [
    { value: "Private", label: __("Private, agents only"), icon: meta.Private.icon },
    {
      value: "Customers",
      label: __("Accessible to customers only"),
      icon: meta.Customers.icon,
    },
    { value: "Public", label: __("Accessible to everyone"), icon: meta.Public.icon },
  ];
});

const access = ref(props.visibility);

watch(show, (open) => {
  if (open) access.value = props.visibility;
});

function publish() {
  emit("publish", access.value!);
  show.value = false;
}
</script>
