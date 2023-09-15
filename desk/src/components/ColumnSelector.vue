<template>
  <NestedPopover>
    <template #target>
      <Button label="Columns" theme="gray" variant="outline">
        <template #prefix>
          <LucideColumns class="h-4 w-4" />
        </template>
        <template #suffix>
          <Badge theme="gray" variant="subtle">
            {{ columns.filter((c) => !hidden.has(c.key)).length }}
          </Badge>
        </template>
      </Button>
    </template>
    <template #body>
      <div class="popover divide-y">
        <Switch
          v-for="c in columns"
          :key="c.key"
          :model-value="!hidden.has(c.key)"
          :label="c.label"
          class="rounded-none first:rounded-t last:rounded-b"
          @update:model-value="toggle(c.key)"
        />
      </div>
    </template>
  </NestedPopover>
</template>

<script setup lang="ts">
import { Badge, Switch } from "frappe-ui";
import { useColumns } from "@/composables/columns";
import { NestedPopover } from "@/components";
import { Column } from "@/types";

interface P {
  doctype: string;
  columns: Column[];
}

const props = defineProps<P>();
const { storage: hidden, toggle } = useColumns(props.doctype);
</script>
