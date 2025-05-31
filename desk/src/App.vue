<template>
  <PortalRoot />
  <Toasts />
  <KeymapDialog />
  <Dialogs />
</template>

<script setup lang="ts">
import { Dialogs } from "@/components/dialogs";
import KeymapDialog from "@/pages/KeymapDialog.vue";
import { useConfigStore } from "@/stores/config";
import { stopSession } from "@/telemetry";
import { createToast } from "@/utils";
import { Toasts } from "frappe-ui";
import { computed, defineAsyncComponent, onMounted, onUnmounted } from "vue";
import { useAuthStore } from "./stores/auth";

useConfigStore();

onMounted(() => {
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
});

const AgentPortalRoot = defineAsyncComponent(
  () => import("@/pages/desk/AgentRoot.vue")
);
const CustomerPortalRoot = defineAsyncComponent(
  () => import("@/pages/CustomerPortalRoot.vue")
);

const PortalRoot = computed(() => {
  const authStore = useAuthStore();
  if (authStore.hasDeskAccess && authStore.isAgent) {
    return AgentPortalRoot;
  } else {
    return CustomerPortalRoot;
  }
});

onUnmounted(() => {
  stopSession();
});
</script>
