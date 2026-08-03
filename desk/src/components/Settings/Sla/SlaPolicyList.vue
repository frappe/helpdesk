<template>
  <div
    v-if="slaPolicyList.list.loading && !slaPolicyList.list.data"
    class="flex items-center justify-center absolute inset-x-0 top-5.5 bottom-0"
  >
    <LoadingIndicator class="w-4" />
  </div>
  <div v-else class="grow">
    <div
      v-if="!slaPolicyList.list.loading && !slaPolicyList.list.data?.length"
      class="flex items-center justify-center absolute inset-x-0 top-5.5 bottom-0"
    >
      <div
        class="p-4 size-14.5 rounded-full bg-surface-gray-1 flex justify-center items-center"
      >
        <ShieldCheck class="size-6 text-ink-gray-6" />
      </div>
      <div class="flex flex-col items-center gap-1">
        <div class="text-base-medium text-ink-gray-6">
          {{ __("No SLA found") }}
        </div>
        <div class="text-p-sm text-ink-gray-5 max-w-60 text-center">
          {{ __("Add one to get started.") }}
        </div>
      </div>
    </div>
    <div v-else class="-ms-2">
      <div
        class="grid grid-cols-6 items-center gap-3 text-sm text-ink-gray-5 ms-2"
      >
        <div class="col-span-5">
          {{ __("Policy name") }}
        </div>
        <div class="col-span-1">{{ __("Enabled") }}</div>
      </div>
      <hr class="mt-2 mx-2" />
      <div v-for="(sla, index) in orderedPolicies" :key="sla.name">
        <SlaPolicyListItem :data="sla" />
        <hr v-if="index !== orderedPolicies.length - 1" class="mx-2" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { dayjs, LoadingIndicator } from "frappe-ui";
import SlaPolicyListItem from "./SlaPolicyListItem.vue";
import { computed, inject } from "vue";
import ShieldCheck from "~icons/lucide/shield-check";
import { SlaPolicy, SlaPolicyListResourceSymbol } from "@/types";

const slaPolicyList = inject(SlaPolicyListResourceSymbol);

// rank 0 means unranked, which is applied last
const rankOrder = (sla: SlaPolicy) => sla.rank || Infinity;

// mirrors the ordering in get_sla (hd_service_level_agreement/utils.py) — keep in sync
const orderedPolicies = computed(() =>
  [...(slaPolicyList.list.data ?? [])].sort(
    (a, b) =>
      Number(a.default_sla) - Number(b.default_sla) ||
      rankOrder(a) - rankOrder(b) ||
      dayjs(a.creation).diff(dayjs(b.creation))
  )
);
</script>
