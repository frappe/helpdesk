<template>
  <div class="flex flex-col">
    <CannedResponseInfo
      class="shrink-0 border-r border-[#F4F5F6]"
      :canned_response="id"
    />
  </div>
</template>

<script setup lang="ts">
import { CannedResponseInfo } from "@/components/canned-response";
defineProps({
  id: {
    type: String,
    required: true,
  },
});
</script>
