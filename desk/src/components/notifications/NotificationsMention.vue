<template>
  <span class="space-x-1 text-gray-700">
    <span class="font-medium text-gray-900">{{ user_from.name }}</span>
    <span>mentioned you in ticket</span>
    <span class="font-medium text-gray-900">{{ reference_ticket }}</span>
  </span>
</template>

<script setup lang="ts">
import { UserInfo } from "@/types";

interface P {
  user_from: UserInfo;
  reference_ticket: string;
}

defineProps<P>();
</script>
