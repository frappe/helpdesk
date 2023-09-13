<template>
  <Popover>
    <template #target="{ togglePopover, isOpen }">
      <Button
        :active="isOpen"
        label="Columns"
        theme="gray"
        variant="outline"
        @click="togglePopover()"
      >
        <template #prefix>
          <LucideColumns class="w-4" />
        </template>
        <template #suffix>
          <Badge theme="gray" variant="subtle">
            {{ columns.filter((c) => !hidden.has(c.key)).length }}
          </Badge>
        </template>
      </Button>
    </template>
    <template #body-main>
      <div class="grid grid-cols-3 gap-2 p-2">
        <Button
          v-for="c in columns"
          :key="c.key"
          :label="c.label"
          :theme="hidden.has(c.key) ? 'gray' : 'blue'"
          class="w-full"
          variant="subtle"
          @click="toggle(c.key)"
        />
      </div>
    </template>
  </Popover>
</template>

<script setup lang="ts">
import { Badge, Popover } from "frappe-ui";
import { useColumns } from "@/composables/columns";
import { Column } from "@/types";

interface P {
  id: string;
  columns: Column[];
}

const props = defineProps<P>();
const { storage: hidden, toggle } = useColumns(props.id);
</script>
