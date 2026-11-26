<template>
  <Layout class="isolate">
    <router-view class="flex flex-1 flex-col overflow-auto" />
  </Layout>
</template>

<script setup lang="ts">
import { useAgentStatusStore } from "@/stores/agentStatus";
import { layoutFor } from "@/components/layouts/layouts";
import { computed } from "vue";

import { useScreenSize } from "@/composables/screen";
// eager: subscribes the availability socket handler and runs the login
// greeting at boot instead of on first ticket open.
useAgentStatusStore();

const { isMobileView } = useScreenSize();

const Layout = computed(() => layoutFor(isMobileView.value));
</script>
