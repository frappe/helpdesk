<template>
  <div class="flex items-center justify-between border-t px-5 py-2">
    <TabButtons
      :buttons="pageLengthOptions.map((o) => ({ label: o }))"
      :model-value="resource.pageLength"
      @update:model-value="
        (val) => {
          resource.update({
            pageLength: val,
          });
          resource.reload();
        }
      "
    />
    <span class="flex items-center gap-1 text-base">
      <LucideLoader2
        v-if="resource.list.loading"
        class="mr-1 inline h-4 w-4 animate-spin"
      />
      <span class="text-gray-900">{{ resource.data?.length }}</span>
      <span class="text-gray-700">of</span>
      <span class="text-gray-900">{{ resource.totalCount }}</span>
    </span>
  </div>
</template>

<script setup lang="ts">
import { TabButtons } from "frappe-ui";
import { Resource } from "@/types";

const pageLengthOptions = [20, 50, 500] as const;
interface P {
  resource: Resource<Array<unknown>>;
}

defineProps<P>();
</script>
