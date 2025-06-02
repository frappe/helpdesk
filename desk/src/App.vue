<template>
  <FrappeUIProvider>
    <PortalRoot />
  </FrappeUIProvider>
  <KeymapDialog />
  <Dialogs />
</template>

<script setup lang="ts">
import { Dialogs } from "@/components/dialogs";
import KeymapDialog from "@/pages/KeymapDialog.vue";
import { useConfigStore } from "@/stores/config";
import { stopSession } from "@/telemetry";
import { FrappeUIProvider, toast } from "frappe-ui";
import { computed, defineAsyncComponent, h, onMounted, onUnmounted } from "vue";
import Wifi from "~icons/lucide/wifi";
import WifiOff from "~icons/lucide/wifi-off";
import { useAuthStore } from "./stores/auth";
useConfigStore();

onMounted(() => {
  window.addEventListener("online", () => {
    toast.create({
      message: "You are now online",
      icon: h(Wifi),
    });
  });

  window.addEventListener("offline", () => {
    toast.create({
      message: "You are now offline",
      icon: h(WifiOff),
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
