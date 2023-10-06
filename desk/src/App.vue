<template>
  <span class="fixed inset-0">
    <RouterView class="antialiased" />
    <Toasts />
    <KeymapDialog />
    <CommandPalette
      v-model:show="commandPalette.show"
      :search-query="commandPalette.query"
      :groups="commandPalette.result"
      @select="({ action }) => action.call() && commandPalette.close()"
    />
  </span>
</template>

<script setup lang="ts">
import { provide, ref, onMounted } from "vue";
import { CommandPalette, Toasts } from "frappe-ui";
import { createToast } from "@/utils";
import { useConfigStore } from "@/stores/config";
import { useCommandPalette } from "@/composables";
import KeymapDialog from "@/pages/KeymapDialog.vue";

useConfigStore();
const commandPalette = useCommandPalette();

const viewportWidth = ref(
  Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0)
);

provide("viewportWidth", viewportWidth);

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
});
</script>
