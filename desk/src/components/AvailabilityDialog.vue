<template>
  <!-- TODO: improve with a BottomSheet on phones -->
  <!-- bare: the panel brings its own row padding, like in the popover -->
  <Dialog v-model:open="open" bare size="sm">
    <template #default="{ close }">
      <div class="p-2 pb-3">
        <div class="flex items-center justify-between pb-1 ps-2">
          <Dialog.Title class="text-lg-semibold text-ink-gray-8">
            {{ __("Set status") }}
          </Dialog.Title>
          <Dialog.Close as-child>
            <Button variant="ghost" icon="lucide-x" :aria-label="__('Close')" />
          </Dialog.Close>
        </div>
        <AvailabilityPanel @close="close" />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { Button, Dialog } from "frappe-ui";
import AvailabilityPanel from "./AvailabilityPanel.vue";

const open = defineModel<boolean>("open", { default: false });
</script>
