<template>
  <Layout class="isolate">
    <router-view class="flex flex-1 flex-col overflow-auto" />
  </Layout>
</template>

<script setup lang="ts">
import { useAgentStatusStore } from "@/stores/agentStatus";
import { computed, defineAsyncComponent } from "vue";

import { useScreenSize } from "@/composables/screen";
// eager: subscribes the availability socket handler and runs the login
// greeting at boot instead of on first ticket open.
useAgentStatusStore();

const { isMobileView } = useScreenSize();

const MobileLayout = defineAsyncComponent(
  () => import("@/components/layouts/MobileLayout.vue")
);
const DesktopLayout = defineAsyncComponent(
  () => import("@/components/layouts/DesktopLayout.vue")
);

const Layout = computed(() => {
  if (isMobileView.value) {
    return MobileLayout;
  } else {
    return DesktopLayout;
  }
});
</script>
