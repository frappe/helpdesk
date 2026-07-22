<template>
  <FrappeUIProvider>
    <router-view />
  </FrappeUIProvider>
  <Dialogs />
</template>

<script setup lang="ts">
import { Dialogs } from "@/components/dialogs";
import { useConfigStore } from "@/stores/config";
import { useFavicon } from "@vueuse/core";
import { FrappeUIProvider, setConfig, toast, useTheme } from "frappe-ui";
import { storeToRefs } from "pinia";
import { h, onMounted } from "vue";
import Wifi from "~icons/lucide/wifi";
import WifiOff from "~icons/lucide/wifi-off";
import { __ } from "./translation";
import { isCustomerPortal, getBrowserTimezone } from "./utils";

const configStore = useConfigStore();
const { favicon } = storeToRefs(configStore);

useFavicon(favicon);

if (!localStorage.getItem("theme")) {
  localStorage.setItem("theme", "light");
}
useTheme();

onMounted(() => {
  window.addEventListener("online", () => {
    toast.create({
      message: __("You are now online."),
      icon: h(Wifi, { class: "text-ink-base" }),
    });
  });

  window.addEventListener("offline", () => {
    toast.create({
      message: __("You are now offline."),
      icon: h(WifiOff, { class: "text-ink-base" }),
    });
  });
  !isCustomerPortal.value && setConfig("localTimezone", window.timezone?.user);
  setConfig("systemTimezone", window.timezone?.system || null);
});
</script>
