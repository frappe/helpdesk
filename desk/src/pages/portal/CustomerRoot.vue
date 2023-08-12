<template>
  <div class="min-h-screen bg-gray-100 p-4">
    <div class="container mx-auto">
      <div
        class="mb-4 flex items-center justify-between rounded bg-white py-2 px-4 shadow"
      >
        <Dropdown :options="options">
          <template #default="{ open }">
            <div
              class="flex cursor-pointer items-center gap-2 rounded-lg text-base text-gray-900"
            >
              <Avatar
                size="sm"
                :image="authStore.userImage"
                :label="authStore.userName"
              />
              {{ authStore.userName }}
              <div class="text-gray-700">
                <Icon v-if="open" icon="lucide:chevron-up" />
                <Icon v-else icon="lucide:chevron-down" />
              </div>
            </div>
          </template>
        </Dropdown>
        <RouterLink :to="{ name: CUSTOMER_PORTAL_LANDING }">
          <img :src="Logo" class="h-5" />
        </RouterLink>
      </div>
      <RouterView />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";
import { Avatar, Dropdown } from "frappe-ui";
import { Icon } from "@iconify/vue";
import { useAuthStore } from "@/stores/auth";
import { CUSTOMER_PORTAL_LANDING, KB_PUBLIC } from "@/router";
import Logo from "@/assets/logos/helpdesk.svg";

const router = useRouter();
const authStore = useAuthStore();

const options = [
  {
    label: "Knowledge Base",
    icon: "book-open",
    onClick: () => {
      const path = router.resolve({ name: KB_PUBLIC });
      window.open(path.href, "_blank");
    },
  },
  {
    label: "My Account",
    icon: "user",
    onClick: () => {
      const protocol = window.location.protocol;
      const domain = window.location.hostname;
      const path = protocol + "//" + domain + "/me";
      window.open(path, "_blank");
    },
  },
  {
    label: "Log out",
    icon: "log-out",
    onClick: () => authStore.logout(),
  },
];
</script>
