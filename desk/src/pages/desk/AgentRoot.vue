<template>
  <Layout>
    <router-view class="z-0 flex flex-1 flex-col overflow-auto" />
  </Layout>
  <CommandPalette />
  <Notifications />
</template>

<script setup lang="ts">
import { computed, defineAsyncComponent, onBeforeMount } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { useConfigStore } from "@/stores/config";
import { CUSTOMER_PORTAL_LANDING, ONBOARDING_PAGE } from "@/router";
import { CommandPalette, Notifications } from "@/components";
import { useScreenSize } from "@/composables/screen";
const router = useRouter();
const authStore = useAuthStore();
const configStore = useConfigStore();

const screenSize = useScreenSize();

const MobileLayout = defineAsyncComponent(
  () => import("@/components/Layouts/MobileLayout.vue")
);
const DesktopLayout = defineAsyncComponent(
  () => import("@/components/Layouts/DesktopLayout.vue")
);
const Layout = computed(() => {
  if (screenSize.width < 640) {
    return MobileLayout;
  } else {
    return DesktopLayout;
  }
});

onBeforeMount(() => {
  if (!authStore.hasDeskAccess) {
    router.replace({ name: CUSTOMER_PORTAL_LANDING });
  }

  if (!configStore.isSetupComplete) {
    router.replace({ name: ONBOARDING_PAGE });
  }
});
</script>
