<template>
  <span class="space-x-1 text-gray-700">
    <span class="font-medium text-gray-900">{{ user.full_name || user }}</span>
    <span>mentioned you in ticket</span>
    <span class="font-medium text-gray-900">{{ props.reference_ticket }}</span>
  </span>
</template>

<script setup lang="ts">
import { useUserStore } from "@/stores/user";

interface P {
  user_from: string;
  reference_ticket: string;
}

const props = defineProps<P>();
const { getUser } = useUserStore();
const user = getUser(props.user_from);
</script>
