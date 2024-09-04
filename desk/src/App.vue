<template>
  <RouterView class="antialiased" />
  <Toasts />
  <KeymapDialog />
</template>

<script setup lang="ts">
import { provide, ref, onMounted, onUnmounted } from "vue";
import { Toasts } from "frappe-ui";
import { createToast } from "@/utils";
import { useConfigStore } from "@/stores/config";
import KeymapDialog from "@/pages/KeymapDialog.vue";
import { stopSession } from "@/telemetry";
import { init as initTelemetry } from "@/telemetry";
useConfigStore();

onMounted(async () => {
  window.addEventListener("online", () => {
    createToast({
      title: "You are now online",
      icon: "wifi",
      iconClasses: "stroke-green-600",
    });
  });

  window.addEventListener("offline", () => {
    createToast({
      title: "You are now offline",
      icon: "wifi-off",
      iconClasses: "stroke-red-600",
    });
  });
  await initTelemetry();
});

onUnmounted(() => {
  stopSession();
});
</script>
