<template>
  <div>
    <div class="flex text-sm text-gray-600 px-2">
      <div class="w-4/5">Policy Name</div>
      <div class="w-1/5">Enabled</div>
    </div>
    <hr class="my-2" />
    <div class="px-2">
      <div
        v-if="slaPolicyListData.data"
        v-for="sla in slaPolicyListData.data"
        :key="sla.name"
      >
        <SlaPolicyListItem :data="sla" />
        <hr class="my-2 -mx-2" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import SlaPolicyListItem from "./SlaPolicyListItem.vue";
import { slaPolicyListData } from "./sla";
</script>
