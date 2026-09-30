<template>
  <div
    v-if="!isSidebarCollapsed"
    class="flex flex-col gap-3 shadow-sm rounded-6 py-2.5 px-3 bg-surface-elevation-2 text-base"
  >
    <div class="inline-flex gap-2 text-ink-gray-9">
      <LucideShieldAlert class="h-4 w-4 my-0.5 shrink-0" />
      <div class="flex flex-col gap-0.5 text-p-sm">
        <div class="font-medium">{{ title }}</div>
        <div class="text-ink-gray-7">{{ description }}</div>
      </div>
    </div>
    <Button :label="__('Learn more')" theme="blue" @click="showDialog = true" />
  </div>
  <Button
    v-else
    variant="ghost"
    :icon="LucideShieldAlert"
    :tooltip="title"
    @click="showDialog = true"
  />
  <Dialog v-model:open="showDialog" :title="dialogTitle">
    <template #default>
      <div class="flex flex-col gap-3 text-p-base text-ink-gray-7">
        <slot />
        <p class="text-p-sm text-ink-gray-5">
          {{ __("You won't see this notice again.") }}
        </p>
      </div>
    </template>
    <template #actions>
      <Button
        class="w-full"
        variant="solid"
        :label="confirmLabel || __('Got it')"
        :loading="confirming"
        @click="confirm"
      />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { type BannerName, useBanners } from "@/composables/useBanners";
import { __ } from "@/translation";
import { ref } from "vue";
import LucideShieldAlert from "~icons/lucide/shield-alert";

const props = defineProps<{
  banner: BannerName;
  title: string;
  description: string;
  dialogTitle: string;
  isSidebarCollapsed: boolean;
  confirmLabel?: string;
  beforeDismiss?: () => Promise<unknown>;
}>();

const { dismiss } = useBanners();
const showDialog = defineModel<boolean>("open", { default: false });
const confirming = ref(false);

async function confirm() {
  confirming.value = true;
  try {
    await props.beforeDismiss?.();
    await dismiss(props.banner);
    showDialog.value = false;
  } catch {
  } finally {
    confirming.value = false;
  }
}
</script>
