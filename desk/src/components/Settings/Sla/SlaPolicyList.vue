<template>
  <div
    v-if="slaPolicyListData.loading && !slaPolicyListData.data"
    class="flex items-center justify-center mt-12"
  >
    <LoadingIndicator class="w-4" />
  </div>
  <div v-else>
    <div
      v-if="slaPolicyListData.data?.length === 0"
      class="flex items-center justify-center rounded-md border border-gray-200 p-4"
    >
      <div class="text-sm text-ink-gray-7">No items in the list</div>
    </div>
    <div v-else>
      <div
        class="grid grid-cols-6 items-center gap-3 text-sm text-gray-600 ml-2"
      >
        <div class="col-span-5">Policy Name</div>
        <div class="col-span-1">Enabled</div>
      </div>
      <hr class="mt-2 mx-2" />
      <div v-for="sla in slaPolicyListData.data" :key="sla.name">
        <SlaPolicyListItem :data="sla" />
        <hr class="mx-2" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { LoadingIndicator } from "frappe-ui";
import SlaPolicyListItem from "./SlaPolicyListItem.vue";
import { slaPolicyListData } from "@/stores/sla";
</script>
