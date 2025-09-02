<template>
  <div class="flex border-b pr-5">
    <div id="app-header" class="flex-1 w-full"></div>
    <div class="flex items-center justify-center">
      <CallUI :userEmail="user" />
    </div>
  </div>
</template>

<script setup>
import CallUI from "@/components/telephony/CallUI.vue";
import { useAuthStore } from "@/stores/auth";

const { user } = useAuthStore();
</script>
