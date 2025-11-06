<template>
  <div
    v-if="slaPolicyList.list.loading && !slaPolicyList.list.data"
    class="flex items-center justify-center mt-12"
  >
    <LoadingIndicator class="w-4" />
  </div>
  <div v-else class="grow">
    <div
      v-if="!slaPolicyList.list.loading && !slaPolicyList.list.data?.length"
      class="flex flex-col items-center justify-center gap-4 h-full"
    >
      <div
        class="p-4 size-14.5 rounded-full bg-surface-gray-1 flex justify-center items-center"
      >
        <ShieldCheck class="size-6 text-ink-gray-6" />
      </div>
      <div class="flex flex-col items-center gap-1">
        <div class="text-base font-medium text-ink-gray-6">
          {{ __("No SLA found") }}
        </div>
        <div class="text-p-sm text-ink-gray-5 max-w-60 text-center">
          {{ __("Add your first SLA to get started.") }}
        </div>
      </div>
      <Button
        :label="__('New')"
        variant="outline"
        icon-left="plus"
        @click="goToNew()"
      />
    </div>
    <div v-else class="-ml-2">
      <div
        class="grid grid-cols-6 items-center gap-3 text-sm text-gray-600 ml-2"
      >
        <div class="col-span-5">
          {{ __("Policy Name") }}
        </div>
        <div class="col-span-1">{{ __("Enabled") }}</div>
      </div>
      <hr class="mt-2 mx-2" />
      <div v-for="(sla, index) in slaPolicyList.list.data" :key="sla.name">
        <SlaPolicyListItem :data="sla" />
        <hr v-if="index !== slaPolicyList.list.data.length - 1" class="mx-2" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Button, LoadingIndicator } from "frappe-ui";
import SlaPolicyListItem from "./SlaPolicyListItem.vue";
import { inject } from "vue";
import { resetSlaData, slaActiveScreen } from "@/stores/sla";
import ShieldCheck from "~icons/lucide/shield-check";
import { SlaPolicyListResourceSymbol } from "@/types";

const slaPolicyList = inject(SlaPolicyListResourceSymbol);

const goToNew = () => {
  resetSlaData();
  slaActiveScreen.value = {
    screen: "view",
    data: null,
    fetchData: true,
  };
};
</script>
