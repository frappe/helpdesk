<template>
  <div
    v-if="!isSidebarCollapsed"
    class="flex flex-col gap-3 shadow-sm rounded-lg py-2.5 px-3 bg-surface-modal text-base"
  >
    <div class="inline-flex gap-2 text-ink-gray-9">
      <LucideShieldAlert class="h-4 w-4 my-0.5 shrink-0" />
      <div class="flex flex-col gap-0.5 text-p-sm">
        <div class="font-medium">
          {{ __("Customer portal update") }}
        </div>
        <div class="text-ink-gray-7">
          {{ __("We have changed how customer portal permissions work") }}
        </div>
      </div>
    </div>
    <Button :label="__('Learn more')" theme="blue" @click="showDialog = true" />
  </div>
  <Button v-else @click="showDialog = true">
    <LucideShieldAlert class="h-4 w-4 shrink-0" />
  </Button>
  <CustomerPortalPermissionDialog v-model="showDialog" />
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { ref } from "vue";
import LucideShieldAlert from "~icons/lucide/shield-alert";
import CustomerPortalPermissionDialog from "./CustomerPortalPermissionDialog.vue";

defineProps({
  isSidebarCollapsed: {
    type: Boolean,
    default: false,
  },
});

const showDialog = ref(false);
</script>
