<template>
  <WhatsAppAccountPage
    v-if="account !== null"
    :key="account || 'new'"
    :name="account"
    @back="account = null"
  />
  <WhatsAppAccounts v-else @open="(name) => (account = name)" />
</template>

<script setup lang="ts">
import { ref } from "vue";
import WhatsAppAccountPage from "./WhatsAppAccountPage.vue";
import WhatsAppAccounts from "./WhatsAppAccounts.vue";

// null shows the list, "" a new account, anything else that account
const account = ref<string | null>(null);
</script>
