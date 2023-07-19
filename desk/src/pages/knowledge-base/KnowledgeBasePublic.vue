<template>
  <div
    ref="elHeaderMaximised"
    class="flex bg-gray-100"
    :style="{
      height: '220px',
    }"
  >
    <div class="container m-auto space-y-2">
      <div
        class="text-3xl font-semibold text-gray-900"
        :style="{
          'font-size': '40px',
        }"
      >
        Knowledge Base
      </div>
      <div
        class="w-max cursor-pointer border-b border-gray-400 pb-1 text-lg text-gray-700 hover:border-gray-800"
        @click="toTickets"
      >
        Track tickets
      </div>
    </div>
  </div>
  <div v-if="!isHeaderVisible" class="sticky top-0 z-50 bg-gray-100">
    <div class="container m-auto flex h-16 items-center justify-between">
      <div class="text-lg font-medium text-gray-900">Knowledge Base</div>
      <div
        class="w-max cursor-pointer border-b border-gray-400 pb-1 text-base text-gray-700 hover:border-gray-800"
        @click="toTickets"
      >
        Track tickets
      </div>
    </div>
  </div>
  <div class="container m-auto">
    <RouterView />
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useElementVisibility } from "@vueuse/core";
import { CUSTOMER_PORTAL_LANDING } from "@/router";

const router = useRouter();
const elHeaderMaximised = ref(null);
const isHeaderVisible = useElementVisibility(elHeaderMaximised);

function toTickets() {
  router.push({
    name: CUSTOMER_PORTAL_LANDING,
  });
}
</script>
