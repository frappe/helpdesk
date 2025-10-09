<template>
  <div
    v-if="slaPolicyList.list.loading && !slaPolicyList.list.data"
    class="flex items-center justify-center mt-12"
  >
    <LoadingIndicator class="w-4" />
  </div>
  <div v-else>
    <div
      v-if="!slaPolicyList.list.loading && !slaPolicyList.list.data?.length"
      class="flex flex-col items-center justify-center gap-4 p-4 h-[500px]"
    >
      <div
        class="p-4 size-14.5 rounded-full bg-surface-gray-1 flex justify-center items-center"
      >
        <ShieldCheck class="size-6 text-ink-gray-6" />
      </div>
      <div class="flex flex-col items-center gap-1">
        <div class="text-base font-medium text-ink-gray-6">No SLA found</div>
        <div class="text-p-sm text-ink-gray-5 max-w-60 text-center">
          Add your first SLA to get started.
        </div>
      </div>
      <Button
        label="Add SLA"
        variant="outline"
        icon-left="plus"
        @click="goToNew()"
      />
    </div>
    <div v-else class="-ml-2">
      <div
        class="grid grid-cols-6 items-center gap-3 text-sm text-gray-600 ml-2"
      >
        <div class="col-span-5">Policy Name</div>
        <div class="col-span-1">Enabled</div>
      </div>
      <hr class="mt-2 mx-2" />
      <div v-for="sla in slaPolicyList.list.data" :key="sla.name">
        <SlaPolicyListItem :data="sla" />
        <hr class="mx-2" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { LoadingIndicator } from "frappe-ui";
import SlaPolicyListItem from "./SlaPolicyListItem.vue";
import { inject } from "vue";
import { resetSlaData, slaActiveScreen } from "@/stores/sla";
import ShieldCheck from "~icons/lucide/shield-check";

const slaPolicyList = inject<any>("slaPolicyList");

const goToNew = () => {
  resetSlaData();
  slaActiveScreen.value = {
    screen: "view",
    data: null,
    fetchData: true,
  };
};
</script>
