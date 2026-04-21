<template>
  <FrappeUIProvider>
    <PortalRoot />
  </FrappeUIProvider>
  <Dialogs />
</template>

<script setup lang="ts">
import { Dialogs } from "@/components/dialogs";
import { useConfigStore } from "@/stores/config";
import { useFavicon } from "@vueuse/core";
import { FrappeUIProvider, setConfig, toast } from "frappe-ui";
import { storeToRefs } from "pinia";
import { computed, defineAsyncComponent, h, onMounted } from "vue";
import Wifi from "~icons/lucide/wifi";
import WifiOff from "~icons/lucide/wifi-off";
import { useAuthStore } from "./stores/auth";
import { __ } from "./translation";
import { isCustomerPortal } from "./utils";

const configStore = useConfigStore();
const { favicon } = storeToRefs(configStore);

useFavicon(favicon);

onMounted(() => {
  window.addEventListener("online", () => {
    toast.create({
      message: __("You are now online."),
      icon: h(Wifi, { class: "text-white" }),
    });
  });

  window.addEventListener("offline", () => {
    toast.create({
      message: __("You are now offline."),
      icon: h(WifiOff, { class: "text-white" }),
    });
  });
  !isCustomerPortal.value && setConfig("localTimezone", window.timezone?.user);
  setConfig("systemTimezone", window.timezone?.system || null);
});

const AgentPortalRoot = defineAsyncComponent(
  () => import("@/roots/AgentRoot.vue")
);
const CustomerPortalRoot = defineAsyncComponent(
  () => import("@/roots/CustomerPortalRoot.vue")
);

const PortalRoot = computed(() => {
  const authStore = useAuthStore();
  if (authStore.hasDeskAccess && authStore.isAgent) {
    return AgentPortalRoot;
  } else {
    return CustomerPortalRoot;
  }
});
</script>
