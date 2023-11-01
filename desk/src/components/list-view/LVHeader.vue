<template>
  <div class="mx-5 rounded bg-gray-100 px-2.5 py-2 text-sm text-gray-600">
    <div class="flex w-full items-center gap-2">
      <FormControl
        v-if="checkbox"
        type="checkbox"
        :model-value="resource.data?.length === selection.storage.size"
        @update:model-value="toggle()"
      />
      <div
        v-for="c in metaState[doctype]?.fields.filter((f) => f.in_list_view)"
        :key="c.fieldname"
      >
        <div v-if="!hiddenColumns.has(c.fieldname)" :class="[c.width]">
          <span :class="[c.align]">
            {{ c.label }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { inject } from 'vue';
import { useColumns } from '@/composables/columns';
import { metaState } from '@/resources';
import { selection } from './selection';
import { CheckboxKey, DocTypeKey, ResourceKey } from './symbols';

const checkbox = inject(CheckboxKey);
const doctype = inject(DocTypeKey);
const resource = inject(ResourceKey);
const { storage: hiddenColumns } = useColumns(doctype);

function toggle() {
  if (selection.storage.size === resource.data.length) {
    selection.storage.clear();
    return;
  }
  resource.data.forEach((d) => selection.storage.add(d.name));
}
</script>
