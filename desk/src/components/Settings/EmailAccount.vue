<template>
  <div
    class="flex justify-between items-center border-b border-gray-200 p-2 cursor-pointer"
  >
    <!-- avatar and name -->
    <div class="flex justify-between items-center gap-2">
      <div
        class="flex h-10 w-10 cursor-pointer items-center justify-center rounded-xl bg-gray-100 hover:bg-gray-200"
      >
        <img :src="emailIcon[emailAccount.service]" class="h-6 w-6" />
      </div>
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

defineProps<{
  emailAccount: EmailAccount;
}>();
</script>

<style scoped></style>
