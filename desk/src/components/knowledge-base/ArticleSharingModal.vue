<template>
  <Dialog v-model:open="show" :title="`${__('Sharing')} “${title}”`">
    <template #default>
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
          />
        </div>

        <div class="flex justify-between">
          <Button
            variant="subtle"
            iconLeft="lucide-link"
            :label="__('Copy link')"
            @click="
              copyToClipboard(url, __('Article link copied to clipboard'))
            "
          />
          <Button variant="solid" :label="__('Publish')" @click="publish" />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { Button, Dialog, Select } from "frappe-ui";
import { ref, watch } from "vue";
import { __ } from "@/translation";
import { copyToClipboard } from "@/utils";

const ACCESS_LEVELS: Record<string, { label: string; icon: string }> = {
  "Agents only": {
    label: __("Accessible to agents only"),
    icon: "lucide-lock",
  },
  "Customers only": {
    label: __("Accessible to customers only"),
    icon: "lucide-building-2",
  },
  Public: { label: __("Accessible to everyone"), icon: "lucide-globe" },
};
const DEFAULT_ACCESS = "Public";

const props = defineProps<{ title: string; visibility: string; url: string }>();
const emit = defineEmits<{ publish: [visibility: string] }>();
const show = defineModel<boolean>({ default: false });

const accessOptions = Object.entries(ACCESS_LEVELS).map(([value, level]) => ({
  value,
  ...level,
}));

const access = ref(DEFAULT_ACCESS);

watch(show, (open) => {
  if (!open) return;
  access.value =
    props.visibility in ACCESS_LEVELS ? props.visibility : DEFAULT_ACCESS;
});

function publish() {
  emit("publish", access.value);
  show.value = false;
}
</script>
