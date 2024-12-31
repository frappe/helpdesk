<template>
  <Layout>
    <router-view class="z-0 flex flex-1 flex-col overflow-auto" />
  </Layout>
</template>

<script setup lang="ts">
import { computed, defineAsyncComponent } from "vue";

import { useScreenSize } from "@/composables/screen";

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
