<template>
  <div class="relative h-full">
    <div v-if="loading" class="space-y-3 px-4 pt-6 sm:px-10 sm:pt-9">
      <Skeleton class="h-7 w-40 rounded-4" />
      <Skeleton v-for="n in 3" :key="n" class="h-24 rounded-6" />
    </div>
    <EmptyState
      v-else-if="failed"
      variant="badge"
      :icon="LucideCloudOff"
      title="Could not load Cloud Settings"
      description="Please contact support."
      :actions="[
        {
          label: __('Contact support'),
          iconLeft: 'lucide-life-buoy',
          href: 'https://support.frappe.io',
        },
      ]"
    />
    <div ref="host" class="h-full" />
  </div>
</template>

<script setup lang="ts">
import EmptyState from "@/components/EmptyState.vue";
import { useBanners } from "@/composables/useBanners";
import { __ } from "@/translation";
import {
  closeCloudSettings,
  openCloudSettings,
  type CloudSettingsPanel,
} from "@frappe/cloud-sdk";
import { Skeleton, toast } from "frappe-ui";
import { onBeforeUnmount, onMounted, ref } from "vue";
import LucideCloudOff from "~icons/lucide/cloud-off";

const props = defineProps<{ panel: CloudSettingsPanel }>();
const host = ref<HTMLElement>();
const loading = ref(true);
const failed = ref(false);
const { refreshTrial } = useBanners();

onMounted(() => {
  openCloudSettings({
    target: host.value,
    panels: [props.panel],
    theme: "auto",
    translate: (message, values) => __(message, values as string[]),
    onClose: props.panel === "billing" ? refreshTrial : undefined,
  })
    .catch((error: Error) => {
      failed.value = true;
      toast.error(error.message || __("Could not open Cloud Settings"));
    })
    .finally(() => (loading.value = false));
});

onBeforeUnmount(closeCloudSettings);
</script>
