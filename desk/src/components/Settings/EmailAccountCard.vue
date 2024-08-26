<template>
  <div
    class="flex justify-between items-center border-b border-gray-200 p-2 cursor-pointer"
  >
    <!-- avatar and name -->
    <div class="flex justify-between items-center gap-2">
      <EmailProviderIcon :logo="emailIcon[emailAccount.service]" />
      <p class="text-gray-700 font-semibold">{{ emailAccount.name }}</p>
    </div>
    <!-- email id -->
    <div>
      <div class="text-sm text-gray-500">{{ emailAccount.email_id }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { EmailAccount } from "@/types";
import { emailIcon } from "./emailConfig";
import EmailProviderIcon from "./EmailProviderIcon.vue";

interface Props {
  emailAccount: EmailAccount;
}

defineProps<Props>();
</script>

<style scoped></style>
