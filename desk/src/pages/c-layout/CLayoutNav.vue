<template>
  <div class="flex items-center justify-between rounded-b bg-white py-2.5 px-5">
    <Dropdown :options="options">
      <template #default="{ open }">
        <div class="flex cursor-pointer items-center gap-1">
          <UserAvatar :user="authStore.userId" expand strong />
          <div class="text-gray-700">
            <Icon v-if="open" icon="lucide:chevron-up" />
            <Icon v-else icon="lucide:chevron-down" />
          </div>
        </div>
      </template>
    </Dropdown>
    <img :src="Logo" class="h-5" />
  </div>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";
import { Dropdown } from "frappe-ui";
import { Icon } from "@iconify/vue";
import { useAuthStore } from "@/stores/auth";
import { UserAvatar } from "@/components";
import Logo from "@/assets/logos/helpdesk.svg";

const router = useRouter();
const authStore = useAuthStore();
const options = [
  {
    label: "Knowledge Base",
    icon: "book-open",
    onClick: () => {
      const path = router.resolve({ name: "KBHome" });
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
