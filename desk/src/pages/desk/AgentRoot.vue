<template>
  <Layout>
    <router-view class="flex flex-1 flex-col overflow-auto" />
  </Layout>
</template>

<script setup lang="ts">
import { useAuthStore } from "@/stores/auth";
import { computed, defineAsyncComponent, onBeforeMount } from "vue";
import { useRouter } from "vue-router";

import { useScreenSize } from "@/composables/screen";
const router = useRouter();
const authStore = useAuthStore();

const { isMobileView } = useScreenSize();

const MobileLayout = defineAsyncComponent(
  () => import("@/components/layouts/MobileLayout.vue")
);
const DesktopLayout = defineAsyncComponent(
  () => import("@/components/layouts/DesktopLayout.vue")
);

const SettingsLayoutDesktop = defineAsyncComponent(
  () => import("@/components/layouts/Settings/SettingsLayoutDesktop.vue")
);

const SettingsLayoutMobile = defineAsyncComponent(
  () => import("@/components/layouts/Settings/SettingsLayoutMobile.vue")
);

const Layout = computed(() => {
  if (isMobileView.value) {
    if (router.currentRoute.value.path.includes("/settings")) {
      return SettingsLayoutMobile;
    }
    return MobileLayout;
  } else {
    if (router.currentRoute.value.path.includes("/settings")) {
      return SettingsLayoutDesktop;
    }
    return DesktopLayout;
  }
});

onBeforeMount(() => {
  if (!authStore.hasDeskAccess) {
    router.replace({ name: "TicketsCustomer" });
  }
});
</script>
