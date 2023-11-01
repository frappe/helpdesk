<template>
  <NestedPopover>
    <template #target>
      <Button label="Columns" theme="gray" variant="outline">
        <template #prefix>
          <LucideColumns class="h-4 w-4" />
        </template>
        <template #suffix>
          <Badge theme="gray" variant="subtle">
            {{ columns.filter((c) => !hidden.has(c.fieldname)).length }}
          </Badge>
        </template>
      </Button>
    </template>
    <template #body>
      <div class="popover divide-y">
        <Switch
          v-for="c in columns"
          :key="c.fieldname"
          :model-value="!hidden.has(c.fieldname)"
          :label="c.label"
          class="rounded-none first:rounded-t last:rounded-b"
          @update:model-value="() => toggle(c.fieldname)"
        />
      </div>
    </template>
  </NestedPopover>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { Switch } from 'frappe-ui';
import { useColumns } from '@/composables/columns';
import { NestedPopover } from '@/components';
import { metaState } from '@/resources';

const props = defineProps<{
  doctype: string;
}>();
const { storage: hidden, toggle } = useColumns(props.doctype);
const columns = computed(
  () => metaState[props.doctype]?.fields.filter((f) => f.in_list_view) || []
);
</script>
