<template>
  <Layout>
    <router-view class="z-0 flex flex-1 flex-col overflow-auto" />
  </Layout>
</template>

<script setup lang="ts">
import { computed, defineAsyncComponent, onBeforeMount } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { useConfigStore } from "@/stores/config";
import { CUSTOMER_PORTAL_LANDING } from "@/router";

import { useScreenSize } from "@/composables/screen";
const router = useRouter();
const authStore = useAuthStore();
const configStore = useConfigStore();

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

onBeforeMount(() => {
  if (!authStore.hasDeskAccess) {
    router.replace({ name: CUSTOMER_PORTAL_LANDING });
  }
});
</script>
