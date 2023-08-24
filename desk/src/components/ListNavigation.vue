<template>
  <div class="flex items-center justify-between border-t px-5 py-2">
    <TabButtons
      :buttons="pageLengthOptions.map((o) => ({ label: o }))"
      :model-value="resource.pageLength"
      @update:model-value="(val: PageLength) => {
        resource.update({
          pageLength: val,
        });
        resource.reload();
      }"
    />
    <Button
      label="Load more"
      theme="gray"
      variant="subtle"
      :disabled="resource.list.loading || !resource.hasNextPage"
      @click="resource.next()"
    >
      <template #prefix>
        <Icon icon="lucide:refresh-cw" />
      </template>
    </Button>
  </div>
</template>

<script setup lang="ts">
import { Button, TabButtons } from "frappe-ui";
import { Icon } from "@iconify/vue";

const pageLengthOptions = [20, 50, 500] as const;
type PageLength = (typeof pageLengthOptions)[number];
interface Resource {
  pageLength: PageLength;
  next: () => void;
  reload: () => void;
  update: (r: Record<string, string | number>) => void;
  hasNextPage?: boolean;
  list?: {
    loading: boolean;
  };
}
interface P {
  resource: Resource;
}

defineProps<P>();
</script>
